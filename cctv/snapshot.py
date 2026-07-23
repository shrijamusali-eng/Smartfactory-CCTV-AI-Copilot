import cv2
import os
from datetime import datetime

SNAPSHOT_DIR = "assets/incidents"

def save_snapshot(frame, worker_id, violation_type):
    # Ensure the assets/incidents directory path exists on disk
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    
    # Generate a precise timestamp string down to microseconds
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{ts}_worker{worker_id}_{violation_type}.jpg"
    path = os.path.join(SNAPSHOT_DIR, filename)
    
    # Use OpenCV to write the raw frame matrix to disk as an image file
    cv2.imwrite(path, frame)
    return path