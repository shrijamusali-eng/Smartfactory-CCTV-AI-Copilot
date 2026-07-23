from database.db import get_active_cameras
from cctv.stream import get_frames
from models.detector import detect
from cctv.tracker import track
from cctv.safety_engine import check
from cctv.incident_pipeline import handle_violations
from cctv.violation_tracker import ViolationTracker


def run_all_cameras(progress_callback=None):
    """
    Process every active camera stored in the database.
    """

    cameras = get_active_cameras()

    if len(cameras) == 0:
        print("No active cameras found.")
        return

    for camera in cameras:

        name = camera["name"]
        zone = camera["zone"]
        source = camera["source_path"]

        print(f"\nStarting {name} ({zone})")

        tracker_instance = ViolationTracker(timeout_seconds=3)

        frames = list(get_frames(source))
        total_frames = len(frames)

        for index, frame in enumerate(frames):

            # ==========================================================
            # YOLO Detection
            # ==========================================================
            results = detect(frame)

            if len(results) == 0:
                continue

            result = results[0]

            # ==========================================================
            # Tracking & Safety Engine Verification
            # ==========================================================
            # FIXED: Correctly passes the YOLO Results object instead of the legacy 'detections'
            tracked = track(result)

            # FIXED: Correctly includes the result.names mapping argument
            violations = check(
                tracked,
                result.names,
            )

            # -------------------------
            # Event Pipeline Dispatch
            # -------------------------
            handle_violations(
                violations=violations,
                frame=frame,
                tracker_instance=tracker_instance,
                camera=name,
                zone=zone,
                is_last_frame=False,
            )

        # ==========================================================
        # Tail-End Buffer Flush
        # ==========================================================
        # Triggers a final boundary check so trailing incidents aren't stuck in tracker memory
        handle_violations(
            violations=[],
            frame=None,
            tracker_instance=tracker_instance,
            camera=name,
            zone=zone,
            is_last_frame=True,
        )

        if progress_callback:
            progress_callback(name)

        print(f"{name} completed.")