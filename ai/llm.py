from langchain_groq import ChatGroq
from app_config import GROQ_API_KEY


class LLMManager:
    """
    Centralized LLM manager.

    Creates reusable Groq models for the application.
    """

    def __init__(self):
        self.fast_llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model="llama-3.1-8b-instant",
            temperature=0
        )

        self.reasoning_llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model="llama-3.3-70b-versatile",
            temperature=0
        )

    def get_fast_llm(self):
        return self.fast_llm

    def get_reasoning_llm(self):
        return self.reasoning_llm


llm_manager = LLMManager()