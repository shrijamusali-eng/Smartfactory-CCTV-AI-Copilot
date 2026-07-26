from datetime import datetime

from database.db import save_event
from cctv.snapshot import save_snapshot
from rag.ingest import add_incident
from cctv.violation_tracker import ViolationTracker

# Explicit severity matrix for easier scaling across multiple PPE types
SEVERITY_MAPPING = {
    "NO-Hardhat": "High",
    "NO-Vest": "High",
    "NO-Mask": "Medium",
    "NO-Goggles": "Medium",
}


# ==========================================================
# Handle Completed Incident
# ==========================================================
def handle_closed_incident(
    record,
    frame,
    camera="Camera 1",
    zone="Zone A",
    run_id=None,
):
    # Quick sanity check on the input record structure
    if not isinstance(record, dict):
        print("❌ Invalid incident payload type received. Skipping.")
        return

    # Check for non-negotiable structural fields needed to build the timeline
    required_keys = {"worker_id", "violation_type", "start_time", "last_seen"}
    if not required_keys.issubset(record):
        missing = required_keys.difference(record)
        print(f"⚠️ Dropping malformed incident record. Missing fields: {missing}")
        return

    # Explicitly enforce clean datetime objects for timeline validation
    try:
        start_time_str = record["start_time"].strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = record["last_seen"].strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate duration safely
        duration = (record["last_seen"] - record["start_time"]).total_seconds()
    except (AttributeError, TypeError) as e:
        print(f"⚠️ Dropping incident due to invalid or malformed timestamps: {e}")
        return

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

    # Safe lookups with sensible default states
    violation_type = record["violation_type"]
    severity = SEVERITY_MAPPING.get(violation_type, "Medium")
    confidence = record.get("confidence", 0.0)

    # Save incident to SQLite
    event_id = save_event(
        camera=camera,
        zone=zone,
        worker_id=record["worker_id"],
        event=violation_type,
        severity=severity,
        confidence=confidence,
        start_time=start_time_str,
        end_time=end_time_str,
        image_path=image_path,
        run_id=run_id,
    )

    # Only ingest into Vector DB if relational record successfully saved
    if event_id is not None:
        print(f"✅ Saved Event ID: {event_id}")

        # Create RAG description
        description = (
            f"Worker {record['worker_id']} "
            f"detected with violation "
            f"{violation_type} "
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
                    "event": violation_type,
                    "severity": severity,
                    "run_id": run_id,
                    "sqlite_event_id": event_id,
                },
            )
        except Exception as e:
            print(f"Gemini skipped: {e}")
            
    else:
        print("⚠️ Skipping RAG ingestion because SQLite primary write failed.")


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
    run_id=None,
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
            run_id=run_id,
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
                run_id=run_id,
            )