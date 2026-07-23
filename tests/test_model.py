from ultralytics import YOLO
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = r"C:\Users\user\Downloads\best.pt"

print("Model path:")
print(MODEL_PATH)
print()

print("File exists:", os.path.exists(MODEL_PATH))
print("File size:", os.path.getsize(MODEL_PATH), "bytes")
print()

model = YOLO(MODEL_PATH)

print("Model classes:")
print(model.names)