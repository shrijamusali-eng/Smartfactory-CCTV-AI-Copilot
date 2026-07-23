import supervision as sv

# ==========================================================
# ByteTrack Tracker
# ==========================================================
tracker = sv.ByteTrack()

# ==========================================================
# Track Objects
# ==========================================================
def track(result):
    """
    Converts YOLO detections into tracked detections using ByteTrack.

    Input:
        result -> Single Ultralytics Results object
                  (results[0] from model.predict())

    Returns:
        supervision.Detections with tracker IDs.
    """

    # Convert YOLO Results -> Supervision Detections
    detections = sv.Detections.from_ultralytics(result)

    print("\n" + "=" * 80)
    print("TRACKER DEBUG")

    print("YOLO Detections:", len(detections))

    if len(detections) == 0:
        print("❌ No detections to track.")
        print("=" * 80)
        return detections

    # Run ByteTrack
    tracked = tracker.update_with_detections(detections)

    print("Tracked Objects:", len(tracked))

    try:
        print("Tracker IDs :", tracked.tracker_id)
    except Exception:
        print("Tracker IDs : None")

    try:
        print("Class IDs   :", tracked.class_id)
    except Exception:
        print("Class IDs   : None")

    print("=" * 80)

    return tracked