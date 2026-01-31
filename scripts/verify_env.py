import torch
import cv2
import fastapi
import ultralytics
import transformers

print("Python OK")
print("Torch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
print("OpenCV:", cv2.__version__)
print("FastAPI:", fastapi.__version__)
print("YOLO:", ultralytics.__version__)
print("Transformers:", transformers.__version__)
