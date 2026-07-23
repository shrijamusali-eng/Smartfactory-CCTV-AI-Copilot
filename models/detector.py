import streamlit as st
from ultralytics import YOLO

@st.cache_resource
def load_model():
    return YOLO("models/best.pt")

model = load_model()

def detect(frame):
    return model.predict(
        source=frame,
        conf=0.35,
        verbose=False,
    )