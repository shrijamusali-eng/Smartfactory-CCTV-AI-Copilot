import os
import json
from datetime import datetime
from langchain_groq import ChatGroq
from app_config import GROQ_API_KEY
from database.db import get_connection
from ai.report_service import ReportService

class AIReportWriter:
    """
    Coordinates metrics extraction, analytical synthesis using Groq (Llama 3.3 70B),
    and PDF report generation into a structured document pipeline.
    """
    
    def __init__(self):
        self.report_service = ReportService()
        # High-capacity model designated for fast text summarization & compliance auditing
        self.report_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=GROQ_API_KEY,
            temperature=0,
        )

    def _gather_report_metrics(self) -> dict:
        """Query the database to pull low-latency analytical counts."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        with get_connection() as conn:
            # 1. Total overview counts
            today_total = conn.execute(
                "SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ?", (today,)
            ).fetchone()[0] or 0
            
            # 2. Breakdown by critical safety events
            helmet_violations = conn.execute(
                "SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ? AND event = 'no-helmet'", (today,)
            ).fetchone()[0] or 0
            
            vest_violations = conn.execute(
                "SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ? AND event = 'no-vest'", (today,)
            ).fetchone()[0] or 0
            
            # 3. Breakdown by high-risk hotspots
            zone_a_incidents = conn.execute(
                "SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ? AND zone = 'Zone A'", (today,)
            ).fetchone()[0] or 0
            
            zone_b_incidents = conn.execute(
                "SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ? AND zone = 'Zone B'", (today,)
            ).fetchone()[0] or 0
            
            # 4. Critical severity counts
            high_severity = conn.execute(
                "SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ? AND severity = 'high'", (today,)
            ).fetchone()[0] or 0

        return {
            "date": today,
            "metrics": {
                "total_today": today_total,
                "helmet_violations": helmet_violations,
                "vest_violations": vest_violations,
                "zone_a_total": zone_a_incidents,
                "zone_b_total": zone_b_incidents,
                "high_severity_count": high_severity
            }
        }

    def generate_daily_report(self) -> str:
        """Compiles metric payloads, generates Llama-3.3 narrative text, and exports a clean PDF."""
        data_payload = self._gather_report_metrics()
        today_str = data_payload["date"]
        
        prompt = f"""You are an expert EHS (Environmental Health and Safety) Director. 
Analyze the following raw safety infrastructure metrics from today and compile a professional, executive-ready safety report.

Metrics JSON:
{json.dumps(data_payload, indent=2)}

You MUST follow this exact Markdown structure so the downstream PDF parser handles layout splits correctly:

## Executive Safety Summary ({today_str})
[Provide a brief high-level summary of the day's security stance and note the calculated risk evaluation status]

### Critical Incident Analysis
[Synthesize the numbers. Address helmet violations ({data_payload['metrics']['helmet_violations']}) and vest violations ({data_payload['metrics']['vest_violations']}) explicitly.]

### Operational Zone Health
[Compare Zone A incidents ({data_payload['metrics']['zone_a_total']}) against Zone B incidents ({data_payload['metrics']['zone_b_total']}). Note immediate floor improvements.]
"""
        
        try:
            # Dispatch directly to Groq Infrastructure
            response = self.report_llm.invoke(prompt)
            narrative_response = response.content
            
            # Formulate clear artifact names
            filename = f"safety_brief_{today_str}.pdf"

            # Parse and serialize text straight into raw binary PDF format
            pdf_result = self.report_service.compile_markdown_to_pdf(
                report_markdown=narrative_response, 
                filename=filename
            )
            return pdf_result
            
        except Exception as e:
            return f"❌ Groq-PDF Generation Pipeline Interrupted: {str(e)}"