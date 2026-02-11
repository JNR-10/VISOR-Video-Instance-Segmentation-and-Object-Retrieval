# Contributing to VISOR

Thank you for your interest in contributing to VISOR! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the behavior
- **Expected behavior**
- **Actual behavior**
- **Screenshots** if applicable
- **Environment details** (OS, Python version, GPU, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** - why is this enhancement useful?
- **Possible implementation** if you have ideas
- **Alternative solutions** you've considered

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow the coding standards** (see below)
3. **Add tests** for new features
4. **Update documentation** as needed
5. **Ensure tests pass** before submitting
6. **Write clear commit messages**

#### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

#### Commit Messages

Follow conventional commits:
```
feat: add video batch processing
fix: resolve segmentation mask alignment issue
docs: update installation instructions
refactor: optimize detection pipeline
```

## Development Setup

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm test
```

## Coding Standards

### Python (Backend)

- Follow **PEP 8** style guide
- Use **type hints** for function parameters and returns
- Write **docstrings** for all public functions/classes
- Keep functions **focused and small**
- Use **meaningful variable names**

Example:
```python
async def process_video(
    video_id: str, 
    video_path: str,
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Process video for object detection and segmentation.
    
    Args:
        video_id: Unique identifier for the video
        video_path: Path to video file
        progress_callback: Optional callback for progress updates
        
    Returns:
        Dictionary containing tracking data and metadata
    """
    # Implementation
    pass
```

### TypeScript (Frontend)

- Use **TypeScript** for all new code
- Follow **React best practices**
- Use **functional components** with hooks
- Keep components **small and focused**
- Use **meaningful prop names**

Example:
```typescript
interface VideoPlayerProps {
  videoUrl: string;
  onProductsFound: (products: Product[]) => void;
}

export default function VideoPlayer({ videoUrl, onProductsFound }: VideoPlayerProps) {
  // Implementation
}
```

## Project Structure

### Adding New Features

#### Backend API Endpoint

1. Create endpoint in `backend/app/api/`
2. Add service logic in `backend/app/services/`
3. Update models in `backend/app/models/` if needed
4. Add tests in `backend/tests/`

#### Frontend Component

1. Create component in `frontend/src/components/`
2. Add types in `frontend/src/types/`
3. Update API client in `frontend/src/lib/api.ts` if needed
4. Add tests in component directory

### ML Model Integration

When adding new ML models:

1. Create service class in `backend/app/services/`
2. Handle model loading and caching
3. Add device detection (CUDA/MPS/CPU)
4. Include error handling
5. Document model requirements in README

Example structure:
```python
class NewModelService:
    def __init__(self):
        self.device = self._get_device()
        self.model = None
        
    def _load_model(self):
        """Lazy load model on first use."""
        if self.model is not None:
            return
        # Load model
        
    def predict(self, input_data):
        """Run inference."""
        self._load_model()
        # Prediction logic
```

## Testing Guidelines

### Backend Tests

- Test all API endpoints
- Test service logic independently
- Mock external dependencies (SerpAPI, etc.)
- Test error handling

### Frontend Tests

- Test component rendering
- Test user interactions
- Test API integration
- Test error states

## Documentation

- Update README.md for user-facing changes
- Update API documentation for endpoint changes
- Add inline comments for complex logic
- Update SETUP.md for installation changes

## Performance Considerations

- Profile code before optimizing
- Consider GPU memory usage
- Optimize video processing pipeline
- Cache expensive computations
- Use async/await for I/O operations

## Questions?

- Open an issue for questions
- Join discussions in GitHub Discussions
- Check existing documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
