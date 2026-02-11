"""Grounding DINO service for zero-shot object detection with text prompts."""

import torch
import numpy as np
from PIL import Image
from typing import List, Tuple, Dict
import cv2

class GroundingDINOService:
    """
    Grounding DINO for open-vocabulary object detection.
    Can detect objects based on text descriptions.
    """
    
    def __init__(self):
        self.device = self._get_device()
        self.model = None
        self.processor = None
        
    def _get_device(self):
        """Get the best available device."""
        # OWL-ViT has issues with MPS (float64 not supported)
        # Use CPU for compatibility
        if torch.cuda.is_available():
            return torch.device("cuda")
        else:
            return torch.device("cpu")
    
    def _load_model(self):
        """Load OWL-ViT model for zero-shot object detection."""
        if self.model is not None:
            return
        
        try:
            from transformers import OwlViTProcessor, OwlViTForObjectDetection
            
            print("Loading OWL-ViT model (zero-shot object detection)...")
            model_id = "google/owlvit-base-patch32"
            
            self.processor = OwlViTProcessor.from_pretrained(model_id)
            self.model = OwlViTForObjectDetection.from_pretrained(model_id)
            self.model.to(self.device)
            
            print(f"Loaded OWL-ViT on {self.device}")
        except Exception as e:
            print(f"Error loading OWL-ViT: {e}")
            raise
    
    def detect_objects(
        self,
        image: np.ndarray,
        text_prompts: List[str],
        score_threshold: float = 0.15
    ) -> List[Dict]:
        """
        Detect objects in image based on text prompts using OWL-ViT.
        
        Args:
            image: Input image (numpy array, BGR format)
            text_prompts: List of object descriptions to detect
            score_threshold: Confidence threshold for detections
            
        Returns:
            List of detections with boxes, labels, and scores
        """
        self._load_model()
        
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
        
        # Prepare text queries (OWL-ViT uses list of queries)
        text_queries = [[prompt] for prompt in text_prompts]
        
        # Process inputs
        inputs = self.processor(
            text=text_queries,
            images=image_pil,
            return_tensors="pt"
        ).to(self.device)
        
        # Run detection
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Post-process results
        target_sizes = torch.tensor([image_pil.size[::-1]]).to(self.device)
        results = self.processor.post_process_object_detection(
            outputs=outputs,
            threshold=score_threshold,
            target_sizes=target_sizes
        )[0]
        
        # Format detections
        detections = []
        
        boxes = results["boxes"].cpu().numpy()
        scores = results["scores"].cpu().numpy()
        labels = results["labels"].cpu().numpy()
        
        for box, score, label_idx in zip(boxes, scores, labels):
            x1, y1, x2, y2 = box
            
            # Get the label text from the prompt index
            label = text_prompts[label_idx] if label_idx < len(text_prompts) else f"object_{label_idx}"
            
            detection = {
                'bbox': {
                    'x': float(x1),
                    'y': float(y1),
                    'width': float(x2 - x1),
                    'height': float(y2 - y1)
                },
                'label': label,
                'confidence': float(score)
            }
            
            detections.append(detection)
        
        return detections
    
    def _apply_nms(self, detections: List[Dict], iou_threshold: float = 0.5) -> List[Dict]:
        """
        Apply Non-Maximum Suppression to remove overlapping detections.
        Keeps the detection with highest confidence when boxes overlap significantly.
        """
        if len(detections) == 0:
            return detections
        
        # Sort by confidence (descending)
        detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        
        keep = []
        
        for i, det in enumerate(detections):
            # Check if this detection overlaps significantly with any kept detection
            should_keep = True
            
            for kept_det in keep:
                iou = self._calculate_iou(det['bbox'], kept_det['bbox'])
                
                # If high overlap, only keep if it's a different class with high confidence
                if iou > iou_threshold:
                    # Keep both if they're different classes and both have good confidence
                    if det['label'] != kept_det['label'] and det['confidence'] > 0.25:
                        continue
                    else:
                        should_keep = False
                        break
            
            if should_keep:
                keep.append(det)
        
        return keep
    
    def _calculate_iou(self, bbox1: Dict, bbox2: Dict) -> float:
        """Calculate Intersection over Union between two bounding boxes."""
        x1_min = bbox1['x']
        y1_min = bbox1['y']
        x1_max = bbox1['x'] + bbox1['width']
        y1_max = bbox1['y'] + bbox1['height']
        
        x2_min = bbox2['x']
        y2_min = bbox2['y']
        x2_max = bbox2['x'] + bbox2['width']
        y2_max = bbox2['y'] + bbox2['height']
        
        # Calculate intersection
        x_inter_min = max(x1_min, x2_min)
        y_inter_min = max(y1_min, y2_min)
        x_inter_max = min(x1_max, x2_max)
        y_inter_max = min(y1_max, y2_max)
        
        if x_inter_max < x_inter_min or y_inter_max < y_inter_min:
            return 0.0
        
        intersection = (x_inter_max - x_inter_min) * (y_inter_max - y_inter_min)
        
        # Calculate union
        area1 = bbox1['width'] * bbox1['height']
        area2 = bbox2['width'] * bbox2['height']
        union = area1 + area2 - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def detect_products(self, image: np.ndarray) -> List[Dict]:
        """
        Detect common products in an image.
        Uses predefined product categories.
        """
        
        # Comprehensive product prompts for accurate classification
        product_prompts = [
            # Computers & Laptops
            "laptop computer", "macbook laptop", "gaming laptop", "notebook computer",
            "desktop computer", "pc tower", "computer monitor", "display screen",
            "ultrawide monitor", "curved monitor",
            
            # Computer Peripherals
            "computer keyboard", "mechanical keyboard", "gaming keyboard", "wireless keyboard",
            "computer mouse", "gaming mouse", "wireless mouse", "trackpad",
            "mouse pad", "keyboard wrist rest",
            
            # Mobile Devices
            "smartphone", "mobile phone", "iphone", "android phone",
            "tablet device", "ipad tablet", "e-reader", "kindle",
            
            # Audio Equipment
            "headphones", "over-ear headphones", "wireless headphones",
            "earbuds", "wireless earbuds", "airpods",
            "bluetooth speaker", "desktop speakers", "speaker system",
            "microphone", "usb microphone", "studio microphone",
            "audio interface", "mixer",
            
            # Camera & Photography
            "digital camera", "dslr camera", "mirrorless camera",
            "webcam", "streaming camera",
            "camera lens", "telephoto lens", "wide angle lens",
            "camera tripod", "monopod", "gimbal stabilizer",
            "ring light", "led panel light", "softbox",
            
            # Office Furniture
            "office desk", "standing desk", "computer desk", "writing desk",
            "office chair", "ergonomic chair", "gaming chair", "desk chair",
            "filing cabinet", "bookshelf", "storage cabinet",
            
            # Lighting
            "desk lamp", "table lamp", "floor lamp", "led lamp",
            "ring light", "studio light", "neon sign",
            
            # Stationery & Books
            "notebook", "journal", "planner", "notepad",
            "book", "textbook", "hardcover book",
            "pen", "pencil", "marker", "highlighter",
            "sticky notes", "paper stack",
            
            # Fashion - Footwear
            "sneakers", "running shoes", "athletic shoes",
            "boots", "dress shoes", "sandals", "slippers",
            
            # Fashion - Clothing
            "t-shirt", "polo shirt", "dress shirt", "button-up shirt",
            "hoodie", "sweatshirt", "sweater", "cardigan",
            "jacket", "leather jacket", "denim jacket", "blazer",
            "jeans", "pants", "trousers", "shorts",
            "dress", "skirt",
            
            # Fashion - Accessories
            "baseball cap", "beanie", "fedora hat", "sun hat",
            "backpack", "messenger bag", "tote bag", "duffel bag",
            "handbag", "purse", "wallet", "clutch",
            "belt", "tie", "bow tie", "scarf",
            "wristwatch", "smartwatch", "fitness tracker",
            "sunglasses", "eyeglasses", "reading glasses",
            "jewelry", "necklace", "bracelet", "ring", "earrings",
            
            # Gaming
            "game controller", "gaming console", "playstation", "xbox",
            "gaming mouse", "gaming keyboard", "gaming headset",
            "gaming chair", "racing sim wheel",
            "nintendo switch", "handheld console",
            
            # Beverages & Drinkware
            "water bottle", "insulated bottle", "sports bottle",
            "coffee mug", "tea cup", "travel mug", "tumbler",
            "wine glass", "beer glass", "champagne glass",
            "thermos", "flask",
            
            # Home Decor
            "potted plant", "succulent plant", "indoor plant",
            "vase", "flower vase", "decorative vase",
            "picture frame", "photo frame", "wall art",
            "wall clock", "desk clock", "alarm clock",
            "candle", "scented candle", "candle holder",
            "throw pillow", "cushion", "decorative pillow",
            "rug", "carpet", "floor mat",
            
            # Kitchen & Dining
            "plate", "dinner plate", "bowl", "serving bowl",
            "fork", "knife", "spoon", "chopsticks",
            "cutting board", "kitchen knife", "chef knife",
            "blender", "coffee maker", "toaster", "kettle",
            "pan", "pot", "cooking pot", "frying pan",
            
            # Sports & Fitness
            "dumbbell", "kettlebell", "weight plate",
            "yoga mat", "exercise mat", "foam roller",
            "resistance band", "jump rope", "pull-up bar",
            "tennis racket", "basketball", "soccer ball", "football",
            "bicycle", "mountain bike", "road bike",
            "skateboard", "longboard", "scooter",
            
            # Tools & Equipment
            "screwdriver", "hammer", "wrench", "pliers",
            "drill", "power drill", "tape measure",
            "toolbox", "tool kit",
            
            # Beauty & Personal Care
            "perfume bottle", "cologne bottle",
            "makeup brush", "cosmetic bag",
            "hair dryer", "hair straightener", "curling iron",
            "electric shaver", "razor",
            
            # Toys & Collectibles
            "action figure", "toy car", "stuffed animal",
            "lego set", "building blocks",
            "board game", "puzzle",
            "collectible figure", "funko pop",
            
            # Musical Instruments
            "guitar", "acoustic guitar", "electric guitar",
            "keyboard", "piano", "digital piano",
            "drum set", "drum pad",
            "ukulele", "violin", "saxophone",
            
            # Storage & Organization
            "storage box", "plastic bin", "storage container",
            "drawer organizer", "cable organizer",
            "laundry basket", "hamper",
            
            # Pet Supplies
            "pet bed", "dog bed", "cat bed",
            "pet bowl", "food bowl", "water bowl",
            "pet toy", "dog toy", "cat toy",
            "pet carrier", "leash", "collar"
        ]
        
        # Detect with higher threshold
        detections = self.detect_objects(image, product_prompts, score_threshold=0.2)
        
        # Apply Non-Maximum Suppression to remove overlapping detections
        detections = self._apply_nms(detections, iou_threshold=0.5)
        
        return detections
