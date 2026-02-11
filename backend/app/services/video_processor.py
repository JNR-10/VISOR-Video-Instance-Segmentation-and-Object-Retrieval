import subprocess
import json
import cv2
import numpy as np
import os
from typing import Dict, List, Optional
from collections import defaultdict

from app.services.grounding_dino_service import GroundingDINOService
from app.services.segmentation_service import SegmentationService
from app.services.product_search import ProductSearchService
from app.core.config import settings

class VideoProcessor:
    def __init__(self):
        self.grounding_dino = GroundingDINOService()
        self.segmentation_service = SegmentationService()
        self.product_search = ProductSearchService()
        self.tracked_objects = {}  # track_id -> detection history
    
    async def extract_metadata(self, video_path: str) -> Dict:
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)
            
            video_stream = next(
                (s for s in data.get('streams', []) if s['codec_type'] == 'video'),
                None
            )
            
            if not video_stream:
                return {}
            
            duration = float(data.get('format', {}).get('duration', 0))
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            
            fps_str = video_stream.get('r_frame_rate', '0/1')
            fps_parts = fps_str.split('/')
            fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 0
            
            return {
                'duration': duration,
                'width': width,
                'height': height,
                'fps': fps
            }
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {}
    
    def _calculate_iou(self, box1, box2):
        """Calculate IoU between two boxes for tracking."""
        x1_min, y1_min = box1['x'], box1['y']
        x1_max, y1_max = x1_min + box1['width'], y1_min + box1['height']
        
        x2_min, y2_min = box2['x'], box2['y']
        x2_max, y2_max = x2_min + box2['width'], y2_min + box2['height']
        
        # Calculate intersection
        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)
        
        if inter_x_max < inter_x_min or inter_y_max < inter_y_min:
            return 0.0
        
        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        
        # Calculate union
        box1_area = box1['width'] * box1['height']
        box2_area = box2['width'] * box2['height']
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
    
    def _assign_track_ids(self, current_detections, previous_detections, next_track_id):
        """Assign track IDs to detections using IoU matching."""
        if not previous_detections:
            # First frame - assign new IDs
            for detection in current_detections:
                detection['track_id'] = next_track_id
                next_track_id += 1
            return current_detections, next_track_id
        
        # Match current detections to previous ones
        matched = set()
        
        for curr_det in current_detections:
            best_iou = 0.3  # Minimum IoU threshold
            best_match = None
            
            for prev_det in previous_detections:
                if prev_det['track_id'] in matched:
                    continue
                
                # Only match same labels
                if curr_det['label'] != prev_det['label']:
                    continue
                
                iou = self._calculate_iou(curr_det['bbox'], prev_det['bbox'])
                
                if iou > best_iou:
                    best_iou = iou
                    best_match = prev_det
            
            if best_match:
                curr_det['track_id'] = best_match['track_id']
                matched.add(best_match['track_id'])
            else:
                # New object
                curr_det['track_id'] = next_track_id
                next_track_id += 1
        
        return current_detections, next_track_id
    
    async def process_video(self, video_id: str, video_path: str, progress_callback=None, log_callback=None) -> Dict:
        """
        Process entire video: detect objects with OWL-ViT, segment with SAM, track them, and find products.
        
        Args:
            progress_callback: Called with (progress_percent, message)
            log_callback: Called with processing log messages
        
        Returns:
            Dict with tracking data for all frames
        """
        print(f"Starting video processing for {video_id}")
        print("Using OWL-ViT (zero-shot detection) + SAM (segmentation) + IoU tracking")
        
        if log_callback:
            await log_callback(f"Starting video processing for {video_id}")
            await log_callback("Using OWL-ViT (zero-shot detection) + SAM (segmentation) + IoU tracking")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Storage for tracking data
        tracks_by_frame = {}  # timestamp_ms -> [detections]
        object_products = {}  # track_id -> product info
        
        # Process every Nth frame (sample rate for performance)
        sample_rate = max(1, int(fps / 2))  # Process 2 frames per second
        
        frame_num = 0
        processed_frames = 0
        next_track_id = 1
        previous_detections = []
        
        # Process frames
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Only process sampled frames
            if frame_num % sample_rate == 0:
                # Detect objects using OWL-ViT
                detections = self.grounding_dino.detect_products(frame)
                
                # Assign track IDs based on IoU matching
                detections, next_track_id = self._assign_track_ids(
                    detections, previous_detections, next_track_id
                )
                
                frame_detections = []
                
                for detection in detections:
                    track_id = detection['track_id']
                    
                    frame_detection = {
                        'track_id': track_id,
                        'bbox': detection['bbox'],
                        'class': detection['label'],
                        'confidence': detection['confidence']
                    }
                    
                    frame_detections.append(frame_detection)
                    
                    # Process new tracks (segment with SAM and find products)
                    if track_id not in object_products:
                        timestamp_ms = int((frame_num / fps) * 1000)
                        product_info = await self._process_tracked_object(
                            frame, detection, track_id, video_id, timestamp_ms
                        )
                        object_products[track_id] = product_info
                        log_msg = f"Track {track_id}: {detection['label']} [OWL-ViT + SAM] -> {product_info['category']}"
                        print(log_msg)
                        if log_callback:
                            await log_callback(log_msg)
                
                # Store frame detections
                timestamp_ms = int((frame_num / fps) * 1000)
                tracks_by_frame[timestamp_ms] = frame_detections
                
                # Update previous detections for next frame
                previous_detections = detections
                
                processed_frames += 1
                
                # Progress callback with detailed message
                if progress_callback:
                    progress = (frame_num / total_frames) * 100
                    message = f"Processing frame {frame_num}/{total_frames} - Found {len(detections)} objects"
                    await progress_callback(progress, message)
            
            frame_num += 1
        
        cap.release()
        
        print(f"Processed {processed_frames} frames, found {len(object_products)} unique objects")
        
        # Save tracking data to JSON
        output_data = {
            'video_id': video_id,
            'fps': fps,
            'total_frames': total_frames,
            'tracks_by_frame': tracks_by_frame,
            'object_products': object_products
        }
        
        # Save to file
        output_path = os.path.join(settings.STORAGE_PATH, 'tracking', f'{video_id}_tracking.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f)
        
        return output_data
    
    async def _process_tracked_object(self, frame, detection, track_id, video_id, timestamp_ms):
        """Process a tracked object: segment with SAM and find products."""
        try:
            category = detection['label']
            bbox = detection['bbox']
            
            # Use SAM to get precise segmentation mask
            # Use bounding box as prompt for better accuracy
            h, w = frame.shape[:2]
            
            # Save frame temporarily for SAM
            temp_frame_dir = os.path.join(settings.STORAGE_PATH, 'temp_frames')
            os.makedirs(temp_frame_dir, exist_ok=True)
            temp_frame_path = os.path.join(temp_frame_dir, f'{video_id}_{track_id}_{timestamp_ms}.jpg')
            cv2.imwrite(temp_frame_path, frame)
            
            # Get segmentation mask from SAM using box prompt
            mask_result = await self.segmentation_service.segment_with_box(
                temp_frame_path,
                bbox,
                video_id,
                timestamp_ms
            )
            
            # Clean up temp frame
            os.remove(temp_frame_path)
            
            # Save mask image to masks directory
            mask_dir = os.path.join(settings.STORAGE_PATH, 'masks', video_id)
            os.makedirs(mask_dir, exist_ok=True)
            mask_filename = f'track_{track_id}_frame_{timestamp_ms}.png'
            mask_path = os.path.join(mask_dir, mask_filename)
            
            # Copy mask from crops to masks directory
            source_mask = mask_result['mask_url'].replace('/static/crops/', '')
            source_mask_path = os.path.join(settings.STORAGE_PATH, 'crops', source_mask)
            if os.path.exists(source_mask_path):
                import shutil
                shutil.copy(source_mask_path, mask_path)
            
            # Search for products
            products = await self.product_search.search_products(category, top_k=1)
            product = products[0] if products else None
            
            return {
                'track_id': track_id,
                'category': category,
                'detection_method': 'owlvit_sam',
                'mask_url': f'/static/masks/{video_id}/{mask_filename}',
                'product': product.model_dump(mode='json') if product else None
            }
        except Exception as e:
            print(f"Error processing track {track_id}: {e}")
            # Fallback without SAM
            products = await self.product_search.search_products(detection['label'], top_k=1)
            product = products[0] if products else None
            return {
                'track_id': track_id,
                'category': detection['label'],
                'detection_method': 'owlvit',
                'product': product.model_dump(mode='json') if product else None
            }
