import re
from datetime import datetime, timedelta
from typing import Dict, Any

class SQLParser:
    """
    Deterministic rule-based regex parser to extract structured SQLite filter criteria
    from natural language user queries without LLM/Graph latency overhead.
    """

    def parse(self, question: str) -> Dict[str, Any]:
        q = question.lower()

        filters = {
            "zone": None,
            "event": None,
            "severity": None,
            "worker_id": None,  # Added structured worker filter mapping
            "start_date": None,
            "end_date": None,
            "limit": 20,
        }

        # -------- Event Normalization --------
        if "helmet" in q:
            filters["event"] = "no-helmet"
        elif "vest" in q or "jacket" in q:
            filters["event"] = "no-vest"

        # -------- Dynamic Zone Extraction --------
        zone_match = re.search(r"zone[- ]?([a-zA-Z0-9]+)", q)
        if zone_match:
            filters["zone"] = f"Zone {zone_match.group(1).upper()}"

        # -------- Severity Identification --------
        if "high severity" in q or "critical" in q or "high" in q:
            filters["severity"] = "high"
        elif "medium severity" in q or "medium" in q:
            filters["severity"] = "medium"
        elif "low severity" in q or "low" in q:
            filters["severity"] = "low"

        # -------- Dynamic Worker ID Extraction --------
        # Captures variations like "worker_12", "worker 45", "worker-7"
        worker_match = re.search(r"worker[-_ ]?(\d+)", q)
        if worker_match:
            filters["worker_id"] = f"worker_{worker_match.group(1)}"

        # -------- Date Range Parsing --------
        today_dt = datetime.now()
        
        if "today" in q:
            today_str = today_dt.strftime("%Y-%m-%d")
            filters["start_date"] = today_str
            filters["end_date"] = today_str
            
        elif "yesterday" in q:
            yesterday_str = (today_dt - timedelta(days=1)).strftime("%Y-%m-%d")
            filters["start_date"] = yesterday_str
            filters["end_date"] = yesterday_str
            
        elif "last week" in q:
            last_week_str = (today_dt - timedelta(days=7)).strftime("%Y-%m-%d")
            filters["start_date"] = last_week_str

        # -------- Row Limit Extraction --------
        limit_match = re.search(r"(?:last|latest|show)\s+(\d+)", q)
        if limit_match:
            filters["limit"] = int(limit_match.group(1))

        return filters