import streamlit as st
from datetime import datetime, timedelta
from database.db import get_connection
from ai.llm import llm_manager

class AIInsightsService:
    """
    Computes hard manufacturing data variances and runs prescriptive reasoning 
    to generate production-ready mitigation insights.
    """
    def __init__(self):
        self.llm = llm_manager.get_fast_llm()

    def _get_raw_telemetry_metrics(self) -> dict:
        """Extracts low-level timeline and location aggregates from the database layer."""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        with get_connection() as conn:
            # 1. Zone ranking by volume
            worst_zone = conn.execute("""
                SELECT zone, COUNT(*) as count 
                FROM events 
                WHERE timestamp >= ? 
                GROUP BY zone 
                ORDER BY count DESC LIMIT 1
            """, (seven_days_ago,)).fetchone()

            # 2. Day-over-day target violation variance
            helmet_today = conn.execute(
                "SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ? AND event = 'no-helmet'", (today,)
            ).fetchone()[0] or 0
            
            helmet_yesterday = conn.execute(
                "SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ? AND event = 'no-helmet'", (yesterday,)
            ).fetchone()[0] or 0

            # 3. Overall critical volume
            high_severity_count = conn.execute("""
                SELECT COUNT(*) FROM events 
                WHERE timestamp >= ? AND severity = 'high'
            """, (seven_days_ago,)).fetchone()[0] or 0

        # Calculate rate variance safely
        if helmet_yesterday > 0:
            pct_change = round(((helmet_today - helmet_yesterday) / helmet_yesterday) * 100, 1)
        else:
            pct_change = 100.0 if helmet_today > 0 else 0.0

        return {
            "top_violation_zone": worst_zone[0] if worst_zone else "None",
            "top_zone_count": worst_zone[1] if worst_zone else 0,
            "helmet_pct_change": pct_change,
            "high_severity_weekly_count": high_severity_count
        }

    def generate_prescriptive_insights(self) -> str:
        """Merges deterministic database math with semantic recommendations."""
        raw_data = self._get_raw_telemetry_metrics()

        # Build prompt using reliable data facts
        system_prompt = (
            "You are the Lead Safety Systems Engineer. Analyze the provided operational data metrics "
            "and output exactly three brief, hard-hitting executive bullet points. "
            "Bullet 1: Call out the highest violation zone. "
            "Bullet 2: Quantify the helmet variance trend. "
            "Bullet 3: Provide two highly specific preventive actions for floor managers. "
            "Be direct. Do not say 'Here are your insights' or use introductory text."
        )
        
        user_data_payload = (
            f"- Highest Violation Zone (7d): {raw_data['top_violation_zone']} ({raw_data['top_zone_count']} events)\n"
            f"- Helmet Compliance Change (YoY/DoD): {raw_data['helmet_pct_change']}%\n"
            f"- High-Severity Events This Week: {raw_data['high_severity_weekly_count']}"
        )

        try:
            response = self.llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_data_payload}
            ])
            return response.content
        except Exception as e:
            return f"❌ Unable to parse predictive insights: {str(e)}"