# VISOR Architecture

## System Overview

VISOR is a full-stack application for creating shoppable video experiences using AI-powered object detection and segmentation.

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Frontend  │────────▶│   Backend   │────────▶│  ML Models  │
│  (Next.js)  │◀────────│  (FastAPI)  │◀────────│  (PyTorch)  │
└─────────────┘         └─────────────┘         └─────────────┘
      │                       │                       │
      │                       │                       │
      ▼                       ▼                       ▼
  Browser UI            File Storage          OWL-ViT + SAM 2
```

## Component Architecture

### Frontend (Next.js 14)

**Technology Stack:**
- React 18 with TypeScript
- Next.js 14 App Router
- TailwindCSS for styling
- HTML5 Canvas for video overlays

**Key Components:**

1. **VideoPlayer** (`components/VideoPlayer.tsx`)
   - Video upload and playback
   - Canvas overlay rendering
   - Object interaction handling
   - Real-time processing status display

2. **ProductPanel** (`components/ProductPanel.tsx`)
   - Display product search results
   - Handle product clicks
   - Show product details

3. **API Client** (`lib/api.ts`)
   - HTTP client for backend communication
   - Type-safe API calls
   - Error handling

**Data Flow:**
```
User Upload → VideoPlayer → API Client → Backend
                ↓
         Processing Status
                ↓
         Tracking Data → Canvas Rendering → Interactive Overlays
```

### Backend (FastAPI)

**Technology Stack:**
- Python 3.10+
- FastAPI for REST API
- PyTorch for ML inference
- OpenCV for video processing

**API Structure:**

```
backend/app/
├── api/              # API endpoints
│   ├── videos.py     # Video upload/management
│   ├── process.py    # Video processing
│   ├── events.py     # Analytics
│   └── products.py   # Product search
├── services/         # Business logic
│   ├── video_processor.py      # Main processing pipeline
│   ├── grounding_dino_service.py  # Object detection
│   ├── segmentation_service.py    # SAM 2 segmentation
│   └── product_search.py          # Product matching
├── core/            # Configuration
│   ├── config.py    # Settings
│   └── database.py  # DB setup (optional)
└── models/          # Data models
```

**Processing Pipeline:**

```
Video Upload
    ↓
Frame Extraction (2 FPS sampling)
    ↓
Object Detection (OWL-ViT)
    ↓
Instance Segmentation (SAM 2)
    ↓
Object Tracking (IoU-based)
    ↓
Product Matching (SerpAPI)
    ↓
Save Tracking Data (JSON)
```

## ML Pipeline

### 1. Object Detection (OWL-ViT)

**Model:** `google/owlvit-base-patch32`

**Purpose:** Zero-shot object detection using text prompts

**Process:**
```python
# Input: Video frame + text prompts
frame = cv2.imread("frame.jpg")
prompts = ["laptop", "mouse", "keyboard", ...]

# Detection
detections = owl_vit.detect(frame, prompts, threshold=0.2)

# Output: Bounding boxes + labels + confidence scores
[
  {"bbox": [x, y, w, h], "label": "laptop", "confidence": 0.85},
  {"bbox": [x, y, w, h], "label": "mouse", "confidence": 0.72},
  ...
]
```

**Optimization:**
- Batch processing of all prompts (230+) in single forward pass
- NMS (Non-Maximum Suppression) to remove overlapping detections
- Confidence threshold filtering (0.2 default)

### 2. Instance Segmentation (SAM 2)

**Model:** `facebook/sam2-hiera-large`

**Purpose:** Generate pixel-accurate masks for detected objects

**Process:**
```python
# Input: Frame + bounding box from detection
bbox = detection["bbox"]

# Segmentation
mask = sam2.segment(frame, bbox)

# Output: Binary mask (H x W)
mask.shape = (1080, 1920)  # Same as frame dimensions
```

**Optimization:**
- Prompt-based segmentation using detection boxes
- Automatic mask quality scoring
- PNG compression for storage

### 3. Object Tracking (IoU-based)

**Algorithm:** Intersection over Union (IoU) matching

**Process:**
```python
# For each new detection
for detection in current_frame_detections:
    # Find best match in previous frame
    best_match = None
    best_iou = 0
    
    for prev_detection in previous_frame_detections:
        iou = calculate_iou(detection.bbox, prev_detection.bbox)
        if iou > best_iou and iou > 0.3:
            best_iou = iou
            best_match = prev_detection
    
    # Assign track ID
    if best_match:
        detection.track_id = best_match.track_id
    else:
        detection.track_id = next_track_id++
```

**Benefits:**
- Simple and fast
- No additional model required
- Works well for short clips

### 4. Product Matching (SerpAPI)

**Service:** Google Shopping API via SerpAPI

**Process:**
```python
# Input: Object label
query = f"{label} buy online"

# Search
results = serpapi.search(query, engine="google_shopping")

# Output: Product listings
[
  {
    "title": "Logitech MX Master 3",
    "price": "$99.99",
    "link": "https://...",
    "thumbnail": "https://..."
  },
  ...
]
```

## Data Storage

### File Structure

```
data/
├── videos/           # Uploaded videos
│   └── {video_id}.mp4
├── masks/            # Segmentation masks
│   └── {video_id}/
│       ├── track_1_frame_0.png
│       ├── track_1_frame_5.png
│       └── ...
└── tracking/         # Tracking data
    └── {video_id}_tracking.json
```

### Tracking Data Format

```json
{
  "video_id": "uuid",
  "fps": 30.0,
  "total_frames": 900,
  "tracks_by_frame": {
    "0": [
      {
        "track_id": 1,
        "bbox": {"x": 100, "y": 200, "width": 300, "height": 400},
        "class": "laptop",
        "confidence": 0.85,
        "mask_path": "/data/masks/uuid/track_1_frame_0.png"
      }
    ],
    "33": [...],
    ...
  },
  "object_products": {
    "1": {
      "label": "laptop",
      "products": [...]
    }
  }
}
```

## Performance Characteristics

### Processing Speed

| Component | Time per Frame | Notes |
|-----------|---------------|-------|
| Frame Extraction | ~10ms | OpenCV |
| OWL-ViT Detection | 200-500ms | GPU-dependent |
| SAM 2 Segmentation | 300-800ms | Per object |
| IoU Tracking | <1ms | CPU-only |
| Total | ~2-5s per frame | With 2-3 objects |

### Memory Usage

| Component | VRAM | RAM |
|-----------|------|-----|
| OWL-ViT | ~2GB | ~1GB |
| SAM 2 | ~4GB | ~2GB |
| Video Buffer | - | ~500MB |
| Total | ~6GB | ~4GB |

### Optimization Strategies

1. **Frame Sampling:** Process 2 FPS instead of 30 FPS
2. **Lazy Loading:** Load models only when needed
3. **Batch Processing:** Process all prompts in single pass
4. **Caching:** Cache model weights in memory
5. **Async Processing:** Background tasks for video processing
6. **NMS:** Reduce duplicate detections

## Scalability Considerations

### Current Limitations

- Single-threaded processing
- In-memory status storage
- No distributed processing
- Local file storage only

### Future Improvements

1. **Horizontal Scaling:**
   - Celery task queue for distributed processing
   - Redis for shared state
   - S3/GCS for file storage

2. **Vertical Scaling:**
   - Multi-GPU support
   - Batch video processing
   - Model quantization (INT8)

3. **Database Integration:**
   - PostgreSQL for metadata
   - pgvector for embeddings
   - Full-text search

## Security Considerations

1. **File Upload:**
   - File type validation
   - Size limits (100MB default)
   - Virus scanning (recommended)

2. **API Security:**
   - CORS configuration
   - Rate limiting (recommended)
   - API key authentication (optional)

3. **Data Privacy:**
   - Automatic cleanup of old files
   - No PII collection
   - Optional encryption at rest

## Deployment Architecture

### Development
```
localhost:3000 (Frontend) → localhost:8000 (Backend) → Local GPU
```

### Production (Recommended)
```
CDN → Next.js (Vercel) → API Gateway → FastAPI (EC2/GCP) → GPU Instance
                                           ↓
                                      S3/GCS Storage
```

## Monitoring & Observability

**Recommended Tools:**
- **Logging:** Python logging + structured logs
- **Metrics:** Prometheus + Grafana
- **Tracing:** OpenTelemetry
- **Error Tracking:** Sentry
- **Performance:** New Relic / DataDog

**Key Metrics:**
- Processing time per video
- Detection accuracy
- API response times
- Error rates
- GPU utilization

## Technology Choices

### Why OWL-ViT?
- Zero-shot detection (no training needed)
- Text-based prompts (flexible categories)
- Good accuracy for common objects
- Reasonable inference speed

### Why SAM 2?
- State-of-the-art segmentation
- Prompt-based (works with detection boxes)
- High-quality masks
- Good performance on diverse objects

### Why FastAPI?
- Async support for long-running tasks
- Automatic API documentation
- Type safety with Pydantic
- Easy integration with ML models

### Why Next.js?
- Server-side rendering
- File-based routing
- Built-in optimization
- Great developer experience
