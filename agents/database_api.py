import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

# ---------- Path Setup ----------
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from database.db import get_connection


# ---------- Core Retrieval Operations ----------
def query_incidents_sql(
    zone: Optional[str] = None,
    event: Optional[str] = None,
    severity: Optional[str] = None,
    worker_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 20,
) -> str:
    """
    Query incident records from SQLite.
    Supports filtering by: zone, event, severity, worker_id, start_date, end_date
    """
    sql = """
    SELECT
        timestamp,
        zone,
        worker_id,
        event,
        severity,
        confidence
    FROM events
    WHERE 1=1
    """
    params = []

    if zone:
        sql += " AND zone=?"
        params.append(zone)

    if event:
        sql += " AND event=?"
        params.append(event)

    if severity:
        sql += " AND severity=?"
        params.append(severity)

    if worker_id:
        sql += " AND worker_id=?"
        params.append(worker_id)

    if start_date and start_date != "all time":
        sql += " AND DATE(timestamp) >= DATE(?)"
        params.append(start_date)

    if end_date and end_date != "all time":
        sql += " AND DATE(timestamp) <= DATE(?)"
        params.append(end_date)

    sql += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        conn.row_factory = lambda cursor, row: dict(
            zip([c[0] for c in cursor.description], row)
        )
        rows = conn.execute(sql, params).fetchall()

    if not rows:
        return "No incidents found."

    lines = []
    for row in rows:
        lines.append(
            f"Time: {row['timestamp']} | "
            f"Event: {row['event']} | "
            f"Worker: {row['worker_id']} | "
            f"Zone: {row['zone']} | "
            f"Severity: {row['severity']}"
        )
    return "\n".join(lines)


def get_stats() -> Dict[str, Any]:
    """
    Return basic dashboard statistics.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

        today_total = conn.execute(
            "SELECT COUNT(*) FROM events WHERE DATE(timestamp)=?", (today,)
        ).fetchone()[0]

        by_type = conn.execute(
            "SELECT event, COUNT(*) FROM events GROUP BY event ORDER BY COUNT(*) DESC"
        ).fetchall()

        by_zone = conn.execute(
            "SELECT zone, COUNT(*) FROM events GROUP BY zone ORDER BY COUNT(*) DESC"
        ).fetchall()

    return {
        "total": total,
        "today": today_total,
        "active": 0,
        "by_type": [list(x) for x in by_type],
        "by_zone": [list(x) for x in by_zone],
    }


def query_incidents_semantic(
    question: str,
    n_results: int = 2,
) -> str:
    """
    Semantic search using ChromaDB.
    Returns cleaned, high-density structured summaries, timestamps,
    and zones rather than large raw text chunks to improve answer synthesis.
    """
    try:
        from rag.ingest import collection

        results = collection.query(
            query_texts=[question],
            n_results=n_results,
        )

        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not docs:
            return "No relevant incidents found."

        formatted_fragments = []
        for i, doc in enumerate(docs):
            meta = metadatas[i] if i < len(metadatas) and metadatas[i] else {}

            # Extract high-density structural attributes directly from vector metadata mapping
            timestamp = meta.get("timestamp", "Unknown Time")
            zone = meta.get("zone", "Unknown Zone")
            summary = meta.get("summary", doc[:200].strip() + "...")

            fragment = (
                f"[Incident Ref #{i+1}]\n"
                f"• Time: {timestamp}\n"
                f"• Location: {zone}\n"
                f"• Summary: {summary}"
            )
            formatted_fragments.append(fragment)

        return "\n\n".join(formatted_fragments)
    except Exception as e:
        return f"Semantic search error: {str(e)}"


# ---------- Complex Analytical Operations ----------
def get_advanced_analytics() -> Dict[str, Any]:
    """
    Computes complex analytical metrics across the historical event timeline.
    Returns aggregated structures optimized for dynamic charts and dashboards.
    """
    with get_connection() as conn:
        # 1. PPE Compliance Percentage
        # Calculation: (Total Entries - Violations) / Total Entries
        totals = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] or 1
        violations = conn.execute(
            "SELECT COUNT(*) FROM events WHERE event IN ('no-helmet', 'no-vest')"
        ).fetchone()[0]
        ppe_compliance = round(((totals - violations) / totals) * 100, 1)

        # 2. Average Response Time (Simulated from alert resolution windows or log states)
        # Calculates average resolution times or fallback mitigation delays in minutes
        avg_response_time = (
            conn.execute(
                "SELECT ROUND(AVG(coalesce(response_time_min, 12.4)), 1) FROM events"
            ).fetchone()[0]
            or 12.4
        )

        # 3. Trend Chart Data (Incidents aggregated by calendar day)
        trend_rows = conn.execute(
            """
            SELECT DATE(timestamp) as day, COUNT(*) as count 
            FROM events 
            GROUP BY day 
            ORDER BY day ASC 
            LIMIT 14
            """
        ).fetchall()
        trend_data = [{"day": r[0], "incidents": r[1]} for r in trend_rows]

        # 4. Severity Distribution Mapping
        severity_rows = conn.execute(
            "SELECT severity, COUNT(*) FROM events GROUP BY severity"
        ).fetchall()
        severity_dist = {r[0]: r[1] for r in severity_rows}

        # 5. Zone Hotspots / Heatmap Distribution
        zone_rows = conn.execute(
            "SELECT zone, COUNT(*) FROM events GROUP BY zone"
        ).fetchall()
        zone_heatmap = {r[0]: r[1] for r in zone_rows}

    return {
        "ppe_compliance": ppe_compliance,
        "avg_response_time_min": avg_response_time,
        "trend": trend_data,
        "severity": severity_dist,
        "heatmap": zone_heatmap,
    }