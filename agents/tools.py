from langchain_core.tools import tool

from agents.database_api import (
    query_incidents_sql,
    query_incidents_semantic,
    get_stats,
)

query_incidents_sql_tool = tool(
    query_incidents_sql,
    description="Query incident records from the safety database.",
)

query_incidents_semantic_tool = tool(
    query_incidents_semantic,
    description="Semantic search over CCTV incidents.",
)

get_stats_tool = tool(
    get_stats,
    description="Return dashboard statistics and safety analytics.",
)