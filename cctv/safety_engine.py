import sys
import os
import urllib.request
import cv2
from ultralytics import YOLO
import streamlit as st

# ==========================================================
# Path Setup
# ==========================================================
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database import db

# ==========================================================
# Model Path & Dynamic Downloader Setup
# ==========================================================
MODEL_DIR = os.path.join(ROOT_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "best.pt")

# Actual GitHub Release download URL or direct storage link
MODEL_URL = "https://github.com/shrijamusali-eng/Smartfactory-CCTV-AI-Copilot/releases/download/v1.0.0/best.pt"

@st.cache_resource
def get_model():
    """
    Lazy-loads the YOLO model. If the weights file is missing (e.g., in cloud deployment),
    it automatically downloads it from the remote URL before loading it.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    if not os.path.exists(MODEL_PATH):
        print(f"📦 Weights file missing at {MODEL_PATH}. Downloading from remote storage...")
        with st.spinner("Downloading AI model weights (this may take a moment on first boot)..."):
            try:
                # Download the weights file dynamically
                urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
                print("✅ Download complete!")
            except Exception as e:
                raise FileNotFoundError(f"Failed to dynamically download model weights: {e}")
                
    return YOLO(MODEL_PATH)


# ==========================================================
# Classes that represent SAFETY VIOLATIONS
# ==========================================================
VIOLATION_LABELS = {
    "no-hardhat",
    "no-mask",
    "no-safety vest",
}

# ==========================================================
# Convert ByteTrack detections into violations
# ==========================================================
def check(tracked, class_names):
    """
    Convert tracked detections into violation dictionaries.
    """
    violations = []

    if tracked is None:
        return violations

    if len(tracked) == 0:
        return violations

    if tracked.tracker_id is None:
        return violations

    print("=" * 70)

    for class_id, tracker_id, confidence in zip(
        tracked.class_id,
        tracked.tracker_id,
        tracked.confidence,
    ):
        if tracker_id is None:
            continue

        # Model class
        label = class_names[int(class_id)].lower().strip()

        print(
            f"Tracker={tracker_id} | "
            f"Label={label} | "
            f"Confidence={confidence:.2f}"
        )

        if label in VIOLATION_LABELS:
            print("✅ VIOLATION DETECTED")
            violations.append(
                {
                    "worker_id": int(tracker_id),
                    "violation_type": label,
                    "confidence": float(confidence),
                }
            )

    print("Violations found:", len(violations))
    print("=" * 70)

    return violations


# ==========================================================
# Optional single-frame processing
# ==========================================================
def process_frame(frame):
    """
    Runs detection on a single frame and stores violations.
    """
    # Use the dynamic model loader
    model_instance = get_model()

    results = model_instance.predict(
        source=frame,
        conf=0.35,
        verbose=False,
    )

    for r in results:
        for box in r.boxes:
            label = model_instance.names[int(box.cls[0])].lower().strip()

            if label in VIOLATION_LABELS:
                db.save_event(
                    zone="Factory_Floor",
                    worker_id=1,
                    event=label,
                    severity="High",
                    confidence=float(box.conf[0]),
                    start_time="now",
                    end_time="now",
                )

    return results