#!/usr/bin/env python3
"""Test script for video processing pipeline."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.video_processor import VideoProcessor

async def test_processing():
    """Test video processing with a sample video."""
    
    # Check if test video exists
    test_video_path = "/Users/spartan/Documents/VISOR/data/videos/test_video.mp4"
    
    if not os.path.exists(test_video_path):
        print(f"❌ Test video not found at: {test_video_path}")
        print("\nPlease:")
        print("1. Create data/videos directory")
        print("2. Add a test video file named 'test_video.mp4'")
        return
    
    print(f"✅ Found test video: {test_video_path}")
    print("\n" + "="*60)
    print("Starting video processing test...")
    print("="*60 + "\n")
    
    processor = VideoProcessor()
    
    # Progress callback
    async def show_progress(progress):
        print(f"Progress: {progress:.1f}%")
    
    try:
        # Process video
        result = await processor.process_video(
            video_id="test_video",
            video_path=test_video_path,
            progress_callback=show_progress
        )
        
        print("\n" + "="*60)
        print("✅ Processing completed successfully!")
        print("="*60 + "\n")
        
        print(f"Video ID: {result['video_id']}")
        print(f"FPS: {result['fps']}")
        print(f"Total Frames: {result['total_frames']}")
        print(f"Processed Frames: {len(result['tracks_by_frame'])}")
        print(f"Unique Objects: {len(result['object_products'])}")
        
        print("\n" + "-"*60)
        print("Detected Objects:")
        print("-"*60)
        
        for track_id, obj_data in result['object_products'].items():
            print(f"\nTrack ID {track_id}:")
            print(f"  Category: {obj_data['category']}")
            print(f"  Detection: {obj_data.get('detection_method', 'unknown')}")
            if obj_data['product']:
                print(f"  Product: {obj_data['product']['title']}")
                print(f"  Price: ${obj_data['product']['price']}")
                print(f"  Buy URL: {obj_data['product']['buy_url']}")
            else:
                print(f"  Product: None found")
        
        print("\n" + "-"*60)
        print("Sample Frame Data (first frame):")
        print("-"*60)
        
        first_timestamp = list(result['tracks_by_frame'].keys())[0]
        first_frame = result['tracks_by_frame'][first_timestamp]
        
        print(f"\nTimestamp: {first_timestamp}ms")
        print(f"Detections: {len(first_frame)}")
        
        for detection in first_frame[:3]:  # Show first 3 detections
            print(f"\n  Track ID: {detection['track_id']}")
            print(f"  Class: {detection['class']}")
            print(f"  Confidence: {detection['confidence']:.2f}")
            print(f"  BBox: x={detection['bbox']['x']:.0f}, y={detection['bbox']['y']:.0f}, "
                  f"w={detection['bbox']['width']:.0f}, h={detection['bbox']['height']:.0f}")
        
        print("\n" + "="*60)
        print("✅ Test completed successfully!")
        print("="*60)
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ Processing failed!")
        print("="*60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_processing())
