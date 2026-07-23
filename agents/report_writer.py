"""
Second agent: turns raw incident data into a prose incident summary.
"""

from langchain_google_genai import ChatGoogleGenerativeAI

from config import GEMINI_API_KEY
from agents.database_api import query_incidents_sql, get_stats

# Gemini model for report writing
report_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0,
)


def write_incident_summary(start_date, end_date):
    """
    Generate a short AI-written executive incident summary.
    """

    # Fetch incidents
    rows = query_incidents_sql(
        start_date=start_date,
        end_date=end_date,
        limit=200,
    )

    # Dashboard statistics
    stats = get_stats()

    prompt = f"""
You are a factory safety officer writing a short executive incident summary.

Write 2-3 professional paragraphs.

Requirements:
- No bullet points.
- Mention the total incidents.
- Mention the most common violation.
- Mention any zone with unusually high incidents.
- Do NOT invent numbers.
- Use only the supplied data.

Time Period:
{start_date} to {end_date}

Total incidents:
{len(rows)}

Overall Statistics:
{stats}

Incident Records:
{rows}
"""

    response = report_llm.invoke(prompt)

    content = response.content

    # Gemini returned plain string
    if isinstance(content, str):
        return content

    # Gemini returned list of blocks
    if isinstance(content, list):

        text = ""

        for block in content:

            if isinstance(block, dict):
                if block.get("type") == "text":
                    text += block.get("text", "")

            elif hasattr(block, "text"):
                text += block.text

            else:
                text += str(block)

        return text.strip()

    # Fallback
    return str(content)