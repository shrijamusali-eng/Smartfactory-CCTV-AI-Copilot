import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

# Load local .env (does nothing if the file isn't present)
load_dotenv()

MODEL_PATH = os.getenv("MODEL_PATH", "models/best.pt")
DATABASE_PATH = os.getenv("DATABASE_PATH", "database/factory_data.db")

# Read the API key from .env first; if not found, use Streamlit Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

print(f"Configuration loaded. Model path set to: {MODEL_PATH}")