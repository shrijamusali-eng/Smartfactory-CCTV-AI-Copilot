import sys
import os
import time
import uuid
import streamlit as st

from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

# ---------- Path Setup ----------
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from agents.tools import (
    query_incidents_sql,
    query_incidents_semantic,
    get_stats,
)

from app_config import GROQ_API_KEY

SYSTEM_PROMPT = """
You are SmartFactory Copilot.

You answer questions about CCTV events, PPE compliance,
factory incidents and safety analytics.

Always use the available tools whenever appropriate.
"""

# ---------- Agent ----------
@st.cache_resource
def get_agent():
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=GROQ_API_KEY,
        temperature=0,
    )

    tools = [
        query_incidents_sql,
        query_incidents_semantic,
        get_stats,
    ]

    memory = MemorySaver()

    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
        checkpointer=memory,
    )


# ---------- Ask ----------
def ask(query: str) -> str:

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())

    agent = get_agent()

    # --- Graceful Error Handling Wrapper ---
    try:
        response = agent.invoke(
            {
                "messages": [
                    HumanMessage(content=query)
                ]
            },
            config={
                "configurable": {
                    "thread_id": st.session_state.thread_id
                }
            },
        )
    except Exception as e:
        if "429" in str(e):
            return "⚠️ AI service is temporarily unavailable. Please try again later."
        return f"❌ {e}"

    content = response["messages"][-1].content

    # Plain string response
    if isinstance(content, str):
        return content

    # LangChain/Gemini list response
    if isinstance(content, list):

        text = ""

        for item in content:

            if isinstance(item, dict):
                if item.get("type") == "text":
                    text += item.get("text", "")

            elif hasattr(item, "text"):
                text += item.text

            else:
                text += str(item)

        return text.strip()

    return str(content)