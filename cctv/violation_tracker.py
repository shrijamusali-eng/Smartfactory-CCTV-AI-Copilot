from datetime import datetime

class ViolationTracker:
    """Keeps track of ongoing violations per worker, so each continuous 
    violation becomes ONE incident instead of one row per frame."""
    
    def __init__(self, timeout_seconds=3):
        self.open_violations = {}  # (worker_id, violation_type) -> dict
        self.timeout_seconds = timeout_seconds

    def update(self, current_violations, frame_time=None):
        """Call this once per frame with the list of violations seen right now.
        Returns a list of CLOSED incidents ready to save."""
        frame_time = frame_time or datetime.now()
        seen_keys = set()
        closed = []

        # 1. Track or update active violations
        for v in current_violations:
            key = (v["worker_id"], v["violation_type"])
            seen_keys.add(key)

            if key not in self.open_violations:
                self.open_violations[key] = {
                    "worker_id": v["worker_id"],
                    "violation_type": v["violation_type"],
                    "confidence": v["confidence"],
                    "start_time": frame_time,
                    "last_seen": frame_time,
                }
            else:
                self.open_violations[key]["last_seen"] = frame_time
                self.open_violations[key]["confidence"] = max(
                    self.open_violations[key]["confidence"], v["confidence"]
                )

        # 2. Close out violations we haven't seen for too long
        stale_keys = []
        for key, record in self.open_violations.items():
            if key not in seen_keys:
                gap = (frame_time - record["last_seen"]).total_seconds()
                if gap > self.timeout_seconds:
                    stale_keys.append(key)

        for key in stale_keys:
            closed.append(self.open_violations.pop(key))

        return closed

    def flush(self):
        """Call this once at the very end of the video to close out 
        any violations still open when the video finished."""
        remaining = list(self.open_violations.values())
        self.open_violations.clear()
        return remaining