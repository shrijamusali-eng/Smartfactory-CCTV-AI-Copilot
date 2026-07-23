import sys
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from database.db import get_connection


def query_incidents_sql(
    zone: Optional[str] = None,
    event: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """
    Query incident records from SQLite.
    Supports filtering by:
    - zone
    - event
    - start_date
    - end_date
    """

    sql = """
    SELECT
        timestamp,
        zone,
        worker_id,
        event,
        severity,
        confidence,
        start_time,
        end_time,
        image_path
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

    # Date filtering
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

    return rows
    


def get_stats() -> Dict[str, Any]:
    """
    Return dashboard statistics.
    """

    today = datetime.now().strftime("%Y-%m-%d")

    with get_connection() as conn:

        total = conn.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0]

        today_total = conn.execute(
            """
            SELECT COUNT(*)
            FROM events
            WHERE DATE(timestamp)=?
            """,
            (today,),
        ).fetchone()[0]

        by_type = conn.execute(
            """
            SELECT event, COUNT(*)
            FROM events
            GROUP BY event
            ORDER BY COUNT(*) DESC
            """
        ).fetchall()

        by_zone = conn.execute(
            """
            SELECT zone, COUNT(*)
            FROM events
            GROUP BY zone
            ORDER BY COUNT(*) DESC
            """
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
    n_results: int = 5,
):
    """
    Semantic search using ChromaDB.
    """

    try:

        from rag.ingest import collection

        return collection.query(
            query_texts=[question],
            n_results=n_results,
        )

    except Exception as e:

        return {
            "error": str(e)
        }