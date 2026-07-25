import re
from typing import Dict, List

class IntentRouter:
    """
    Data-driven intent router that classifies queries using exact phrase matrices
    with regex word-boundaries, minimizing LLM token overhead for deterministic lookups.
    """
    
    ROUTES: Dict[str, List[str]] = {
        "report": [
            "report", "generate report", "safety report", "executive brief", 
            "write a report", "daily summary report", "pdf export", "executive summary"
        ],
        "stats": [
            "dashboard", "real-time dashboard", "live monitoring", "stats", 
            "statistics", "summary", "overview", "graph", "chart", "metrics",
            "live numbers", "telemetry"
        ],
        "insights": [
            "insights", "recommend preventive actions", "safety recommendations",
            "give me insights", "what should we fix", "action items", "improvement tips"
        ],
        "semantic": [
            "explain", "why did", "how come", "describe", "historical logs",
            "operator notes", "similar incidents", "context surrounding", "details of"
        ],
        "comparison": [
            "compare", "delta", "day-over-day", "weekly", "shift", "trends"
        ],
        "risk": [
            "high risk", "explain risk", "danger", "hazard", "unsafe", "root cause", "threat"
        ],
        "sql": [
            "select", "where", "limit", "filter incidents", "raw database",
            "helmet", "vest", "incident", "violations", "zone", "count", 
            "total", "today", "yesterday", "severity"
        ]
    }

    def route(self, query: str) -> str:
        """Matches query tokens against dynamic route definitions; fallbacks to 'general'."""
        normalized = query.lower().strip()
        
        for intent, keywords in self.ROUTES.items():
            for keyword in keywords:
                # \b guarantees we match full words only (e.g., matching 'vest' but not 'invest')
                if re.search(r'\b' + re.escape(keyword) + r'\b', normalized):
                    return intent
                    
        return "general"