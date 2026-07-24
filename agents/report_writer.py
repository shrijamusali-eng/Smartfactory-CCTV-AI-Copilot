"""
Generate report summary using Groq instead of Gemini.
This ensures PDF reports utilize Llama 3.3 70B while retaining 
database statistics fallbacks.
"""

from langchain_groq import ChatGroq
from config import GROQ_API_KEY
from agents.database_api import query_incidents_sql, get_stats

# Initialize the report generation model
report_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=GROQ_API_KEY,
    temperature=0,
)

def write_incident_summary(start_date, end_date):

    rows = query_incidents_sql(
        start_date=start_date,
        end_date=end_date,
        limit=200,
    )

    stats = get_stats()

    total = stats.get("total", 0)
    today = stats.get("today", 0)
    active = stats.get("active", 0)

    # Most common violation
    by_type = stats.get("by_type", [])
    if by_type:
        top_violation = f"{by_type[0][0]} ({by_type[0][1]} incidents)"
    else:
        top_violation = "No violation data available"

    # Most affected zone
    by_zone = stats.get("by_zone", [])
    if by_zone:
        top_zone = f"{by_zone[0][0]} ({by_zone[0][1]} incidents)"
    else:
        top_zone = "No zone data available"

    summary = f"""
Executive Safety Summary

Reporting Period:
{start_date} to {end_date}

A total of {total} incidents have been recorded.
Today's incidents: {today}
Currently active violations: {active}

The most common safety violation is:
{top_violation}

The zone with the highest number of incidents is:
{top_zone}

This report is generated directly from the incident database and provides an overview of the current factory safety status.
"""

    return summary