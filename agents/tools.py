# agents/tools.py
from langchain_core.tools import tool
from agents.database_api import get_stats, query_incidents_sql
from ai.semantic_search_service import SemanticSearchService

# Instantiate dependencies locally inside tools module safely
semantic_svc = SemanticSearchService()

@tool
def get_stats_tool():
    """Fetches real-time factory safety and inspection statistics."""
    return get_stats()

@tool
def query_incidents_sql_tool(zone: str = None, event: str = None, severity: str = None):
    """Queries structural data using criteria filters for exact matching logs."""
    return query_incidents_sql(zone=zone, event=event, severity=severity)

@tool
def query_incidents_semantic_tool(query: str):
    """Searches through natural language log notes and contextual descriptions."""
    return semantic_svc.retrieve_concise_evidence(query=query)