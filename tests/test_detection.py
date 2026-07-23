import sys
import os
from datetime import datetime

# Setup paths so your execution terminal maps folders correctly
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from cctv.stream import get_frames
from models.detector import detect, model
from cctv.tracker import track
from cctv.safety_engine import check

# Import your Day 2 dual-storage memory modules
from database.db import init_db, save_event
from cctv.snapshot import save_snapshot
from rag.ingest import add_incident

# Spin up database tables if running fresh
init_db()

video_path = os.path.join(root_dir, "data", "factory.mp4")
print("Starting complete unified video safety monitoring pipeline...")

for frame in get_frames(video_path):
    results = detect(frame)
    tracked = track(results)
    violations = check(tracked, model.names)
    
    if violations:
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for tracker_id, label in violations:
            print(f"⚠️ Incident Found! Tracking ID {tracker_id} -> {label}")
            
            # A. Extract and write the frame snapshot JPG file to disk
            img_path = save_snapshot(frame, worker_id=int(tracker_id), violation_type=label)
            
            # B. Save structural analytics log to SQLite
            save_event(
                timestamp=timestamp_str,
                camera="Cam-Main",
                zone="Assembly Line A",
                worker_id=int(tracker_id),
                event=label,
                severity="High",
                image_path=img_path
            )
            
            # C. Ingest human-readable context sentence into ChromaDB for the AI Agent
            readable_text = f"At {timestamp_str}, Worker {tracker_id} committed a {label} violation in Assembly Line A."
            metadata_payload = {
                "timestamp": timestamp_str,
                "worker_id": int(tracker_id),
                "event": label,
                "zone": "Assembly Line A"
            }
            add_incident(text=readable_text, metadata=metadata_payload)