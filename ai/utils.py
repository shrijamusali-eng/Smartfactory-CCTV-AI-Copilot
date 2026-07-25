from typing import Any

def format_stats(stats: dict) -> str:
    """
    Format raw statistics maps into a standardized, scannable plaintext dashboard snapshot.
    """
    text = f"""📊 Factory Dashboard

Total Incidents: {stats['total']}
Today's Incidents: {stats['today']}
Active Incidents: {stats['active']}

Top Event Types:"""

    for event, count in stats.get("by_type", []):
        text += f"\n• {event}: {count}"

    text += "\n\nTop Zones:\n"

    for zone, count in stats.get("by_zone", []):
        text += f"\n• {zone}: {count}"

    return text


def extract_response(content: Any) -> str:
    """
    Extract and norm text contents cleanly from assorted LLM response message frames.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text = []
        for item in content:
            if isinstance(item, dict):
                text.append(item.get("text", ""))
            elif hasattr(item, "text"):
                text.append(item.text)
            else:
                text.append(str(item))
        return "".join(text).strip()

    return str(content)