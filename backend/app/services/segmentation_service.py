import torch
import numpy as np
from PIL import Image
import os
import cv2
from typing import Dict, Tuple, Optional
import hashlib

from app.core.config import settings

class SegmentationService:
    def __init__(self):
        self.device = self._get_device()
        self.model = None
        self.predictor = None
        self.clip_model = None
        self.clip_processor = None
        self.crops_dir = os.path.join(settings.STORAGE_PATH, "crops")
        os.makedirs(self.crops_dir, exist_ok=True)
        self._load_clip()
    
    def _get_device(self):
        if settings.DEVICE == "mps" and torch.backends.mps.is_available():
            return torch.device("mps")
        elif torch.cuda.is_available():
            return torch.device("cuda")
        else:
            return torch.device("cpu")
    
    def _load_clip(self):
        """Load CLIP model for object classification."""
        if self.clip_model is not None:
            return
        
        try:
            from transformers import CLIPProcessor, CLIPModel
            
            # Use larger CLIP model for better accuracy
            # Options: 
            # - openai/clip-vit-base-patch32 (base, faster)
            # - openai/clip-vit-large-patch14 (large, more accurate)
            model_name = "openai/clip-vit-large-patch14"
            
            print(f"Loading CLIP model ({model_name})...")
            self.clip_model = CLIPModel.from_pretrained(model_name)
            self.clip_processor = CLIPProcessor.from_pretrained(model_name)
            self.clip_model.to(self.device)
            print(f"Loaded CLIP on {self.device}")
        except Exception as e:
            print(f"Error loading CLIP: {e}")
            raise
    
    def _load_model(self):
        if self.model is not None:
            return
        
        try:
            from sam2.build_sam import build_sam2
            from sam2.sam2_image_predictor import SAM2ImagePredictor
            
            # Get absolute path to project root (parent of backend dir)
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            project_root = os.path.dirname(backend_dir)
            model_path = os.path.join(project_root, "data", "models", "sam2_hiera_base_plus.pt")
            
            if not os.path.exists(model_path):
                print(f"Model not found at {model_path}. Please download sam2_hiera_base_plus.pt")
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # SAM 2 config for base model
            model_cfg = "sam2_hiera_b+.yaml"
            
            self.model = build_sam2(model_cfg, model_path, device=self.device)
            self.predictor = SAM2ImagePredictor(self.model)
            
            print(f"Loaded SAM 2 on {self.device}")
        except ImportError as e:
            print(f"SAM 2 not installed. Error: {e}")
            print("Install with: pip install git+https://github.com/facebookresearch/segment-anything-2.git")
            raise
    
    def _classify_object(self, crop_image):
        """Classify the segmented object using CLIP."""
        from PIL import Image
        import torch
        
        # Comprehensive product categories for all types of objects
        categories = [
            # Electronics & Devices
            "laptop", "computer", "desktop computer", "monitor", "screen",
            "smartphone", "phone", "tablet", "iPad",
            "keyboard", "mouse", "webcam", "camera",
            "headphones", "earbuds", "speakers",
            "microphone", "mic", "studio microphone",
            "charger", "cable", "USB cable",
            
            # Office & Studio Equipment
            "desk", "office desk", "table",
            "chair", "office chair", "gaming chair",
            "lamp", "desk lamp", "ring light", "LED light",
            "tripod", "camera tripod", "phone stand",
            "notebook", "journal", "planner",
            "pen", "pencil", "marker",
            "book", "textbook",
            
            # Fashion & Apparel
            "shoes", "sneakers", "boots", "sandals", "slippers",
            "shirt", "t-shirt", "hoodie", "jacket", "coat", "sweater",
            "pants", "jeans", "shorts", "skirt", "dress",
            "hat", "cap", "beanie",
            "bag", "backpack", "purse", "handbag", "briefcase",
            "watch", "smartwatch", "fitness tracker",
            "sunglasses", "glasses", "eyeglasses",
            "jewelry", "necklace", "bracelet", "ring",
            "belt", "tie", "scarf",
            
            # Home & Lifestyle
            "water bottle", "coffee mug", "cup", "thermos",
            "plant", "potted plant", "succulent",
            "clock", "wall clock",
            "picture frame", "poster", "artwork",
            "pillow", "cushion",
            "blanket", "throw blanket",
            
            # Gaming & Entertainment
            "game controller", "gaming mouse", "gaming keyboard",
            "VR headset", "console",
            
            # Fitness & Sports
            "dumbbell", "yoga mat", "resistance band",
            "water bottle", "gym bag",
            
            # Other Common Items
            "bottle", "can", "container",
            "box", "package",
            "remote control",
            "power bank",
            "wallet", "purse"
        ]
        
        # Prepare text prompts
        text_inputs = self.clip_processor(
            text=[f"a photo of {cat}" for cat in categories],
            return_tensors="pt",
            padding=True
        ).to(self.device)
        
        # Prepare image
        image_inputs = self.clip_processor(
            images=crop_image,
            return_tensors="pt"
        ).to(self.device)
        
        # Get predictions
        with torch.no_grad():
            image_features = self.clip_model.get_image_features(**image_inputs)
            text_features = self.clip_model.get_text_features(**text_inputs)
            
            # Normalize features
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # Calculate similarity
            similarity = (image_features @ text_features.T).squeeze(0)
            probs = similarity.softmax(dim=0)
            
            # Get top prediction
            top_idx = probs.argmax().item()
            confidence = probs[top_idx].item()
            
            return categories[top_idx], confidence
    
    def _classify_object_with_context(self, crop_image, yolo_class: str):
        """
        Classify object using CLIP with YOLO class as context.
        Narrows down categories based on YOLO detection for better accuracy.
        """
        import torch
        
        # Map YOLO classes to relevant CLIP categories
        yolo_to_categories = {
            'laptop': ['laptop', 'computer', 'MacBook', 'notebook computer', 'gaming laptop'],
            'cell phone': ['smartphone', 'phone', 'iPhone', 'Android phone', 'mobile phone'],
            'keyboard': ['keyboard', 'mechanical keyboard', 'gaming keyboard', 'wireless keyboard'],
            'mouse': ['mouse', 'gaming mouse', 'wireless mouse', 'computer mouse'],
            'tv': ['TV', 'television', 'monitor', 'screen', 'display'],
            'remote': ['remote control', 'TV remote'],
            'book': ['book', 'textbook', 'notebook', 'journal', 'magazine'],
            'clock': ['clock', 'wall clock', 'desk clock', 'alarm clock'],
            'vase': ['vase', 'flower vase', 'ceramic vase'],
            'potted plant': ['potted plant', 'plant', 'succulent', 'indoor plant', 'houseplant'],
            'chair': ['chair', 'office chair', 'gaming chair', 'desk chair', 'armchair'],
            'couch': ['couch', 'sofa', 'loveseat', 'sectional'],
            'bottle': ['water bottle', 'bottle', 'thermos', 'sports bottle', 'reusable bottle'],
            'cup': ['cup', 'coffee mug', 'mug', 'tea cup', 'travel mug'],
            'backpack': ['backpack', 'bag', 'school bag', 'hiking backpack', 'laptop bag'],
            'handbag': ['handbag', 'purse', 'tote bag', 'shoulder bag'],
            'tie': ['tie', 'necktie', 'bow tie'],
            'umbrella': ['umbrella', 'rain umbrella', 'compact umbrella'],
            'suitcase': ['suitcase', 'luggage', 'travel bag', 'carry-on'],
        }
        
        # Get relevant categories for this YOLO class, or use all if not mapped
        if yolo_class in yolo_to_categories:
            categories = yolo_to_categories[yolo_class]
        else:
            # Fallback: use YOLO class name and some generic variations
            categories = [
                yolo_class,
                f"{yolo_class} product",
                f"modern {yolo_class}",
                f"professional {yolo_class}",
                f"premium {yolo_class}"
            ]
        
        # Prepare text prompts
        text_inputs = self.clip_processor(
            text=[f"a photo of {cat}" for cat in categories],
            return_tensors="pt",
            padding=True
        ).to(self.device)
        
        # Prepare image
        image_inputs = self.clip_processor(
            images=crop_image,
            return_tensors="pt"
        ).to(self.device)
        
        # Get predictions
        with torch.no_grad():
            image_features = self.clip_model.get_image_features(**image_inputs)
            text_features = self.clip_model.get_text_features(**text_inputs)
            
            # Normalize features
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # Calculate similarity
            similarity = (image_features @ text_features.T).squeeze(0)
            probs = similarity.softmax(dim=0)
            
            # Get top prediction
            top_idx = probs.argmax().item()
            confidence = probs[top_idx].item()
            
            return categories[top_idx], confidence
    
    async def segment_with_box(
        self,
        frame_path: str,
        bbox: Dict[str, float],
        video_id: str,
        timestamp_ms: int
    ) -> Dict:
        """Segment object using bounding box prompt for precise segmentation."""
        self._load_model()
        
        image = cv2.imread(frame_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        self.predictor.set_image(image_rgb)
        
        # Convert bbox to SAM format [x1, y1, x2, y2]
        input_box = np.array([
            bbox['x'],
            bbox['y'],
            bbox['x'] + bbox['width'],
            bbox['y'] + bbox['height']
        ])
        
        # Use box prompt for more accurate segmentation
        masks, scores, logits = self.predictor.predict(
            point_coords=None,
            point_labels=None,
            box=input_box[None, :],
            multimask_output=False
        )
        
        mask = masks[0]
        confidence = float(scores[0])
        
        mask_filename = f"{video_id}_{timestamp_ms}_mask.png"
        mask_path = os.path.join(self.crops_dir, mask_filename)
        self._save_mask(mask, mask_path)
        
        return {
            "bbox": bbox,
            "mask_url": f"/static/crops/{mask_filename}",
            "confidence": confidence
        }
    
    async def segment(
        self,
        frame_path: str,
        click_x: float,
        click_y: float,
        video_id: str,
        timestamp_ms: int
    ) -> Dict:
        self._load_model()
        
        image = cv2.imread(frame_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        self.predictor.set_image(image_rgb)
        
        point_coords = np.array([[click_x, click_y]])
        point_labels = np.array([1])
        
        masks, scores, logits = self.predictor.predict(
            point_coords=point_coords,
            point_labels=point_labels,
            multimask_output=True
        )
        
        best_idx = np.argmax(scores)
        mask = masks[best_idx]
        confidence = float(scores[best_idx])
        
        bbox = self._mask_to_bbox(mask)
        
        mask_filename = f"{video_id}_{timestamp_ms}_mask.png"
        mask_path = os.path.join(self.crops_dir, mask_filename)
        self._save_mask(mask, mask_path)
        
        crop_filename = f"{video_id}_{timestamp_ms}_crop.png"
        crop_path = os.path.join(self.crops_dir, crop_filename)
        crop_image = self._create_crop(image_rgb, mask, bbox)
        cv2.imwrite(crop_path, cv2.cvtColor(crop_image, cv2.COLOR_RGB2BGR))
        
        embedding = self._generate_embedding(crop_image)
        
        # Classify the object
        from PIL import Image
        crop_pil = Image.fromarray(crop_image)
        object_category, classification_confidence = self._classify_object(crop_pil)
        
        return {
            "bbox": bbox,
            "mask_url": f"/static/crops/{mask_filename}",
            "crop_url": f"/static/crops/{crop_filename}",
            "confidence": confidence,
            "embedding": embedding,
            "category": object_category,
            "category_confidence": classification_confidence
        }
    
    def _mask_to_bbox(self, mask: np.ndarray) -> Dict[str, float]:
        y_indices, x_indices = np.where(mask)
        
        if len(x_indices) == 0 or len(y_indices) == 0:
            return {"x": 0, "y": 0, "width": 0, "height": 0}
        
        x_min, x_max = float(x_indices.min()), float(x_indices.max())
        y_min, y_max = float(y_indices.min()), float(y_indices.max())
        
        return {
            "x": x_min,
            "y": y_min,
            "width": x_max - x_min,
            "height": y_max - y_min
        }
    
    def _save_mask(self, mask: np.ndarray, path: str):
        mask_img = (mask * 255).astype(np.uint8)
        cv2.imwrite(path, mask_img)
    
    def _create_crop(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        bbox: Dict[str, float],
        padding: int = 20
    ) -> np.ndarray:
        x, y = int(bbox["x"]), int(bbox["y"])
        w, h = int(bbox["width"]), int(bbox["height"])
        
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(image.shape[1], x + w + padding)
        y2 = min(image.shape[0], y + h + padding)
        
        crop = image[y1:y2, x1:x2].copy()
        crop_mask = mask[y1:y2, x1:x2]
        
        crop_rgba = np.zeros((crop.shape[0], crop.shape[1], 4), dtype=np.uint8)
        crop_rgba[:, :, :3] = crop
        crop_rgba[:, :, 3] = (crop_mask * 255).astype(np.uint8)
        
        target_size = 336
        scale = min(target_size / crop_rgba.shape[1], target_size / crop_rgba.shape[0])
        new_w = int(crop_rgba.shape[1] * scale)
        new_h = int(crop_rgba.shape[0] * scale)
        
        resized = cv2.resize(crop_rgba, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        
        final = np.ones((target_size, target_size, 4), dtype=np.uint8) * 255
        final[:, :, 3] = 0
        
        y_offset = (target_size - new_h) // 2
        x_offset = (target_size - new_w) // 2
        final[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        return final[:, :, :3]
    
    def _generate_embedding(self, crop: np.ndarray) -> Optional[list]:
        try:
            from transformers import CLIPProcessor, CLIPModel
            
            if not hasattr(self, 'clip_model'):
                self.clip_model = CLIPModel.from_pretrained(settings.CLIP_MODEL)
                self.clip_processor = CLIPProcessor.from_pretrained(settings.CLIP_MODEL)
                self.clip_model.to(self.device)
            
            pil_image = Image.fromarray(crop)
            inputs = self.clip_processor(images=pil_image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(**inputs)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten().tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
