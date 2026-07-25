# agents/copilot.py
import os
import sys
import uuid
import streamlit as st

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# ---------- Path Setup ----------
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import raw Python functions for low-latency direct router bypass paths
from agents.database_api import (
    get_stats,
    query_incidents_sql,
)

# Decoupled Core Service Layers
from ai.intent_router import IntentRouter
from ai.sql_parser import SQLParser
from ai.report_writer import AIReportWriter
from ai.analytics_service import AnalyticsService
from ai.risk_service import RiskService
from ai.semantic_search_service import SemanticSearchService

from ai.llm import llm_manager
from ai.utils import format_stats, extract_response

SYSTEM_PROMPT = """
You are SmartFactory AI Copilot.

You answer questions about:
- PPE compliance
- CCTV incidents
- Worker safety
- Factory analytics

Rules:
1. Use only ONE tool whenever possible.
2. Use SQL tools for counts, trends and statistics.
3. Use semantic search only for explanations or similar incidents.
4. If the answer is obvious, respond directly.
5. Keep responses concise and clear.
"""

# Instantiate architectural services at the module layer
router = IntentRouter()
parser = SQLParser()
writer = AIReportWriter()
analytics_svc = AnalyticsService()
risk_svc = RiskService()
semantic_search_svc = SemanticSearchService()


# ---------- Caching Optimization ----------
@st.cache_data(ttl=10)
def get_cached_stats():
    """Bypasses active database disk-reads for rapid repeated client requests."""
    return get_stats()


# ---------- Agent Factory ----------
@st.cache_resource
def get_agent():
    """Generates the LangGraph ReAct agent loop with an isolated memory checkpointer.
    Deferred internal imports isolate execution to prevent circular context initialization loops.
    """
    from agents.tools import (
        get_stats_tool,
        query_incidents_semantic_tool,
        query_incidents_sql_tool,
    )
    
    llm = llm_manager.get_fast_llm()
    tools = [
        query_incidents_sql_tool,
        query_incidents_semantic_tool,
        get_stats_tool,
    ]
    memory = MemorySaver()

    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
        checkpointer=memory,
    )


# ---------- Ask Execution Flow ----------
def ask(query: str) -> str:
    """Routes and executes user queries across deterministic paths or AI agents."""
    intent = router.route(query)

    try:
        # Route 1: Instant structured AI report generator track (Groq Llama 3.3 + PDF)
        if intent == "report":
            return writer.generate_daily_report()

        # Route 2: Instant dashboard metrics snapshot bypass
        elif intent == "stats":
            return format_stats(get_cached_stats())

        # Route 3: Fast-Track Metadata-Aware Semantic Search Bypass
        elif intent == "semantic":
            return semantic_search_svc.retrieve_concise_evidence(query=query)

        # Route 4: Low-latency deterministic SQL parser bypass
        elif intent == "sql" or intent == "incidents":
            # Direct shortcut check: if no filter keywords exist, return global sql pool overview
            keywords = ["zone", "event", "severity", "worker", "after", "before", "between"]
            if not any(kw in query.lower() for kw in keywords):
                return str(query_incidents_sql())
            
            # Extract filters deterministically via service engine
            filters = parser.parse(query)
            return query_incidents_sql(**filters)

        # Route 5: Analytics and Day-Over-Day Comparative Deltas
        elif intent == "comparison":
            metrics = analytics_svc.compute_daily_deltas()
            return analytics_svc.generate_delta_narrative(metrics)

        # Route 6: Incident Threat Evaluation & Risk Analysis
        elif intent == "risk":
            return risk_svc.evaluate_incident_threat(query)

        # Route 7: Deep reasoning conversational fallback loop (LangGraph)
        if "thread_id" not in st.session_state:
            st.session_state.thread_id = str(uuid.uuid4())

        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        agent = get_agent()

        # Fetch and manage conversation historical memory window state
        state = agent.get_state(config)
        existing_messages = state.values.get("messages", []) if state.values else []

        MAX_MESSAGES = 10 
        if len(existing_messages) > MAX_MESSAGES:
            truncated_history = existing_messages[-MAX_MESSAGES:]
            agent.update_state(config, {"messages": truncated_history})

        # Process the new query against the graph state
        response = agent.invoke(
            {"messages": [HumanMessage(content=query)]},
            config=config,
        )

        content = response["messages"][-1].content

        # Handle diverse variant LangGraph object return schemas safely
        if isinstance(content, str):
            return extract_response(content)

        if isinstance(content, list):
            text = ""
            for item in content:
                if isinstance(item, dict):
                    text += item.get("text", "")
                elif hasattr(item, "text"):
                    text += item.text
                else:
                    text += str(item)
            return extract_response(text.strip())

        return extract_response(str(content))

    except Exception as e:
        # Rate-limiting / API window saturation graceful degradation
        if "429" in str(e):
            return "⚠️ AI service is temporarily unavailable. Please try again later."
        return f"❌ {e}"