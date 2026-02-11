# VISOR - Video Instance Segmentation & Object Retrieval

<div align="center">

![VISOR Demo](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![License](https://img.shields.io/badge/License-MIT-green)

**AI-powered shoppable video platform for Instagram-style content**

[Features](#features) • [Demo](#demo) • [Installation](#installation) • [Usage](#usage) • [Architecture](#architecture)

</div>

---

## 🎯 Overview

VISOR transforms regular videos into interactive shoppable experiences. Upload a video, and VISOR automatically:

- 🔍 **Detects** 230+ product categories using zero-shot AI (OWL-ViT)
- ✂️ **Segments** objects with pixel-perfect masks (SAM 2)
- 🎯 **Tracks** objects across frames with IoU-based tracking
- 🛍️ **Matches** products to real shopping results
- 🎨 **Overlays** interactive highlights on the video

Perfect for content creators, e-commerce platforms, and social media applications.

## ✨ Features

### Current Implementation
- ✅ **Zero-Shot Object Detection** - Detects 230+ product types without training
- ✅ **Instance Segmentation** - Pixel-accurate object masks using SAM 2
- ✅ **Multi-Object Tracking** - IoU-based tracking across video frames
- ✅ **Real-Time Processing** - Progress updates and live logs during processing
- ✅ **Vertical Video Support** - Optimized for Instagram/TikTok format
- ✅ **Interactive Overlays** - Click objects to see product matches
- ✅ **Product Search** - Integration with SerpAPI for real shopping results
- ✅ **Stateless Mode** - Works without database for easy deployment

### Supported Product Categories
Electronics • Fashion • Home Decor • Sports & Fitness • Gaming • Beauty • Kitchen • Office • Toys • Musical Instruments • Pet Supplies • and more...

## 🎬 Demo

https://github.com/yourusername/visor/assets/demo.gif

## 🏗️ Architecture

### Detection Pipeline
```
Video Upload → Frame Sampling → OWL-ViT Detection → SAM 2 Segmentation → IoU Tracking → Product Matching
```

### Tech Stack

**Frontend**
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **Video**: HTML5 Canvas API
- **Icons**: Lucide React

**Backend**
- **Framework**: FastAPI (Python 3.10+)
- **ML Models**: 
  - **OWL-ViT** (google/owlvit-base-patch32) - Zero-shot object detection
  - **SAM 2** (facebook/sam2-hiera-large) - Instance segmentation
  - **CLIP** - Product embeddings (optional)
- **Video Processing**: OpenCV, FFmpeg
- **Product Search**: SerpAPI
- **Storage**: Local filesystem (stateless mode)

**Infrastructure**
- **GPU Support**: CUDA, MPS (Apple Silicon), CPU fallback
- **Deployment**: Standalone or Docker
- **Database**: Optional PostgreSQL (currently disabled for portability)

## Project Structure

```
VISOR/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Config, database
│   │   ├── models/      # ML model wrappers
│   │   ├── services/    # Business logic
│   │   └── schemas/     # Pydantic models
│   ├── tests/
│   └── requirements.txt
├── frontend/            # Next.js frontend
│   ├── src/
│   │   ├── app/        # App router pages
│   │   ├── components/ # React components
│   │   ├── lib/        # Utilities
│   │   └── types/      # TypeScript types
│   ├── public/
│   └── package.json
├── data/               # Local data storage
│   ├── videos/
│   ├── frames/
│   ├── crops/
│   └── models/         # Downloaded model weights
├── scripts/            # Utility scripts
└── docker/             # Docker configs (optional)
```

## 📦 Installation

### Prerequisites
- **Python 3.10+** (3.11 recommended)
- **Node.js 18+** 
- **FFmpeg** (for video processing)
- **Git**
- **GPU** (optional but recommended): CUDA-compatible GPU or Apple Silicon

### Quick Start

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/visor.git
cd visor
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create data directories
mkdir -p data/videos data/masks data/tracking

# Set up environment variables
cp .env.example .env
# Edit .env and add your SERPAPI_KEY for product search
```

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

#### 4. Verify Installation

```bash
# Run verification script
python scripts/verify_env.py
```

## 🚀 Usage

### Start the Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### Start the Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### Using the Application

1. **Upload a Video**
   - Click the upload area or drag & drop a video file
   - Supported formats: MP4, MOV, WebM
   - Recommended: Short clips (10-30 seconds) for faster processing

2. **Processing**
   - Video is automatically processed upon upload
   - Watch real-time progress and detection logs
   - Processing time: ~2-5 seconds per second of video

3. **Interact with Objects**
   - Play the video to see detected objects highlighted
   - Click on any highlighted object to see product matches
   - Browse similar products from online retailers

### Configuration

**Backend Configuration** (`backend/.env`):
```env
# API Keys
SERPAPI_KEY=your_serpapi_key_here

# Storage
STORAGE_PATH=./data

# Model Settings
DEVICE=auto  # auto, cuda, mps, or cpu
CONFIDENCE_THRESHOLD=0.2
```

**Frontend Configuration** (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📚 API Documentation

### Video Management

**Upload Video**
```http
POST /api/videos
Content-Type: multipart/form-data

file: <video_file>
```

Response:
```json
{
  "video_id": "uuid",
  "url": "/data/videos/uuid.mp4",
  "filename": "video.mp4"
}
```

### Video Processing

**Start Processing**
```http
POST /api/process
Content-Type: application/json

{
  "video_id": "uuid"
}
```

**Get Processing Status**
```http
GET /api/process/status/{video_id}
```

Response:
```json
{
  "video_id": "uuid",
  "status": "processing",
  "progress": 45.5,
  "message": "Processing frame 45/100 - Found 3 objects",
  "logs": [
    "Track 1: laptop [OWL-ViT + SAM] -> laptop",
    "Track 2: mouse [OWL-ViT + SAM] -> mouse"
  ]
}
```

**Get Tracking Data**
```http
GET /api/tracking/{video_id}
```

### Product Search

**Search Products**
```http
POST /api/products/search
Content-Type: application/json

{
  "query": "gaming mouse",
  "limit": 10
}
```

### Analytics

**Log Event**
```http
POST /api/events
Content-Type: application/json

{
  "event_type": "object_click",
  "video_id": "uuid",
  "data": {}
}
```

Full API documentation available at: `http://localhost:8000/docs`

## ⚙️ Configuration & Optimization

### Detection Accuracy

Adjust confidence thresholds in `backend/app/services/grounding_dino_service.py`:

```python
# Higher = fewer false positives, may miss some objects
score_threshold=0.2  # Default: 0.2 (range: 0.1-0.5)

# NMS threshold for overlapping detections
iou_threshold=0.5    # Default: 0.5 (range: 0.3-0.7)
```

### Performance Optimization

**GPU Acceleration**
- **CUDA**: Automatically used if available
- **Apple Silicon (MPS)**: Automatically used on M1/M2/M3 Macs
- **CPU Fallback**: Works on any system (slower)

**Processing Speed**
- Frame sampling: 2 FPS (configurable in `video_processor.py`)
- Detection: ~200-500ms per frame
- Segmentation: ~300-800ms per frame
- Total: ~2-5 seconds per second of video

**Memory Usage**
- OWL-ViT: ~2GB VRAM
- SAM 2: ~4GB VRAM
- Total recommended: 8GB+ VRAM or 16GB+ RAM

### Custom Product Categories

Add custom prompts in `backend/app/services/grounding_dino_service.py`:

```python
product_prompts = [
    # Your custom categories
    "custom product", "specific item", "brand name",
    # ...
]
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm test
```

## 🐛 Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'torch'"**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

**"CUDA out of memory"**
- Reduce frame sampling rate
- Use smaller SAM model variant
- Process shorter video clips

**"No objects detected"**
- Lower confidence threshold (0.15-0.2)
- Check if objects are in supported categories
- Ensure good video quality and lighting

**Frontend can't connect to backend**
- Verify backend is running on port 8000
- Check CORS settings in `backend/app/main.py`
- Ensure `NEXT_PUBLIC_API_URL` is set correctly

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for all frontend code
- Add tests for new features
- Update documentation as needed
- Keep commits atomic and well-described

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OWL-ViT** by Google Research - Zero-shot object detection
- **SAM 2** by Meta AI - Segment Anything Model
- **Transformers** by Hugging Face - Model implementations
- **FastAPI** - Modern Python web framework
- **Next.js** - React framework for production

## 📧 Contact

For questions, issues, or suggestions:
- Open an issue on GitHub
- Email: your.email@example.com
- Twitter: @yourusername

## 🗺️ Roadmap

- [ ] Real-time video streaming support
- [ ] Mobile app (React Native)
- [ ] Custom model training interface
- [ ] Multi-language support
- [ ] Cloud deployment templates (AWS, GCP, Azure)
- [ ] Batch video processing
- [ ] Analytics dashboard
- [ ] Webhook integrations

---

<div align="center">

**Made with ❤️ for the creator economy**

[⬆ Back to Top](#visor---video-instance-segmentation--object-retrieval)

</div>
