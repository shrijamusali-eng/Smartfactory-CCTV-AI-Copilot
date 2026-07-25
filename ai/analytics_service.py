from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from database.db import get_connection
from ai.llm import llm_manager

class AnalyticsService:
    """Handles low-latency calculation matrices, trend analysis, and historical window differentials."""

    def compute_daily_deltas(self) -> Dict[str, Any]:
        """Calculates precise event counts across 24-hour comparative matrices via raw SQL."""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        with get_connection() as conn:
            t_total = conn.execute("SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ?", (today,)).fetchone()[0] or 0
            t_ppe = conn.execute("SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ? AND event IN ('no-helmet', 'no-vest')", (today,)).fetchone()[0] or 0
            
            y_total = conn.execute("SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ?", (yesterday,)).fetchone()[0] or 0
            y_ppe = conn.execute("SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ? AND event IN ('no-helmet', 'no-vest')", (yesterday,)).fetchone()[0] or 0

        delta_total = t_total - y_total
        pct_change = round((delta_total / y_total) * 100, 1) if y_total > 0 else (100.0 if delta_total > 0 else 0.0)

        return {
            "today_total": t_total,
            "today_ppe_violations": t_ppe,
            "yesterday_total": y_total,
            "yesterday_ppe_violations": y_ppe,
            "absolute_change": delta_total,
            "percentage_change": pct_change
        }

    def generate_delta_narrative(self, metrics: Dict[str, Any]) -> str:
        """Converts completed calculation structures into human-readable operations insights."""
        sign = "+" if metrics["absolute_change"] >= 0 else ""
        
        prompt = f"""You are an executive operations analyst. Review these calculated day-over-day manufacturing facility metrics:
- Today's Total Incidents: {metrics['today_total']} (PPE Violations: {metrics['today_ppe_violations']})
- Yesterday's Total Incidents: {metrics['yesterday_total']} (PPE Violations: {metrics['yesterday_ppe_violations']})
- Computed Shift: {sign}{metrics['absolute_change']} absolute change ({sign}{metrics['percentage_change']}%).

Write a concise 3-sentence summary highlighting structural factory safety improvements or critical risk exposures."""
        
        llm = llm_manager.get_fast_llm()
        return llm.invoke(prompt).content