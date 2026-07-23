import sys
import os
from ultralytics import YOLO

# ==========================================================
# Path Setup
# ==========================================================
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database import db

# ==========================================================
# Load PPE Model
# ==========================================================
model = YOLO("models/best.pt")

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

    results = model.predict(
        source=frame,
        conf=0.35,
        verbose=False,
    )

    for r in results:

        for box in r.boxes:

            label = model.names[int(box.cls[0])].lower().strip()

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