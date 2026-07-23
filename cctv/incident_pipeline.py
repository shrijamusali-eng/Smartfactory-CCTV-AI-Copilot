from datetime import datetime

from database.db import save_event
from cctv.snapshot import save_snapshot
from rag.ingest import add_incident
from cctv.violation_tracker import ViolationTracker


# ==========================================================
# Handle Completed Incident
# ==========================================================
def handle_closed_incident(
    record,
    frame,
    camera="Camera 1",
    zone="Zone A",
):

    print("=" * 60)
    print("🔥 CLOSED INCIDENT")
    print(record)
    print("=" * 60)

    image_path = ""

    # Save snapshot if available
    if frame is not None:
        image_path = save_snapshot(
            frame,
            record["worker_id"],
            record["violation_type"],
        )

    # Determine severity
    severity = (
        "High"
        if record["violation_type"] == "NO-Hardhat"
        else "Medium"
    )

    start_time_str = record["start_time"].strftime("%Y-%m-%d %H:%M:%S")
    end_time_str = record["last_seen"].strftime("%Y-%m-%d %H:%M:%S")

    # Save incident to SQLite
    event_id = save_event(
        camera=camera,
        zone=zone,
        worker_id=record["worker_id"],
        event=record["violation_type"],
        severity=severity,
        confidence=record["confidence"],
        start_time=start_time_str,
        end_time=end_time_str,
        image_path=image_path,
    )

    print(f"✅ Saved Event ID: {event_id}")

    # Calculate duration
    duration = (
        record["last_seen"] - record["start_time"]
    ).total_seconds()

    # Create RAG description
    description = (
        f"Worker {record['worker_id']} "
        f"detected with violation "
        f"{record['violation_type']} "
        f"on {camera} "
        f"in {zone} lasting "
        f"{duration:.0f} seconds."
    )

    # Store in Vector Database
    try:
        add_incident(
            description,
            metadata={
                "camera": camera,
                "worker_id": record["worker_id"],
                "zone": zone,
                "event": record["violation_type"],
                "severity": severity,
            },
        )

    except Exception as e:
        print(f"Gemini skipped: {e}")


# ==========================================================
# Process Violations
# ==========================================================
def handle_violations(
    violations,
    frame,
    tracker_instance=None,
    camera="Camera 1",
    zone="Zone A",
    is_last_frame=False,
):

    # Create tracker if one isn't provided
    if tracker_instance is None:

        if not hasattr(handle_violations, "_tracker"):
            handle_violations._tracker = ViolationTracker()

        tracker_instance = handle_violations._tracker

    print(f"Frame Violations: {len(violations)}")

    closed = tracker_instance.update(violations)

    print(f"Closed Incidents: {len(closed)}")

    # Save completed incidents
    for incident in closed:
        handle_closed_incident(
            record=incident,
            frame=frame,
            camera=camera,
            zone=zone,
        )

    # Flush remaining incidents when video ends
    if is_last_frame:

        remaining = tracker_instance.flush()

        print(f"Flushed Incidents: {len(remaining)}")

        for incident in remaining:
            handle_closed_incident(
                record=incident,
                frame=frame,
                camera=camera,
                zone=zone,
            )