import sys
import os
import tempfile
import uuid
import cv2
import logging
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

# Instantiate module-scoped logger to enable granular filtering control
logger = logging.getLogger(__name__)

# ==========================================================
# Path Setup
# ==========================================================
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ==========================================================
# Imports
# ==========================================================
from database.db import init_db, get_connection
from agents.copilot import ask
from agents.tools import get_stats

from cctv.safety_engine import check, get_model
from cctv.incident_pipeline import handle_violations
from cctv.violation_tracker import ViolationTracker
from cctv.multi_camera_runner import run_all_cameras

from reports.generate_report import generate_pdf_report

# ==========================================================
# Initialize Database & Diagnostic Checks
# ==========================================================
init_db()

# ==========================================================
# Streamlit Configuration
# ==========================================================
st.set_page_config(
    page_title="SmartFactory CCTV Copilot",
    page_icon="🏭",
    layout="wide",
)

st.title("🏭 SmartFactory CCTV Safety Monitor & AI Copilot")
st.markdown("---")

# ==========================================================
# Layout
# ==========================================================
left_col, right_col = st.columns([2, 1])

# ==========================================================
# LEFT PANEL - VIDEO ANALYTICS
# ==========================================================
with left_col:
    st.header("📹 CCTV Safety Monitoring")

    mode = st.radio(
        "Detection Mode",
        [
            "Upload Video",
            "Registered Cameras",
        ],
    )

    uploaded_file = None
    if mode == "Upload Video":
        uploaded_file = st.file_uploader(
            "Upload CCTV Footage",
            type=["mp4", "avi", "mov"],
        )

    if uploaded_file:
        temp_video = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp4"
        )
        temp_video.write(uploaded_file.read())
        temp_video.close()

        st.video(temp_video.name)

        if st.button(
            "🚀 Run Safety Detection",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner("Processing CCTV footage..."):
                processing_succeeded = False
                try:
                    from cctv.stream import get_frames
                    from cctv.tracker import track

                    # Dynamic metadata retrieval using OpenCV to capture precise track bounds
                    cap = cv2.VideoCapture(temp_video.name)
                    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    cap.release()
                    
                    # Diagnostic warning handling using our module-scoped logger
                    if total_video_frames <= 0:
                        logger.warning(
                            f"Could not read CAP_PROP_FRAME_COUNT from file {uploaded_file.name}. "
                            f"Defaulting processing bar denominator metrics to 300."
                        )
                        total_video_frames = 300

                    yolo_model = get_model()
                    tracker = ViolationTracker(timeout_seconds=3)

                    # Unique Run Tag generation to isolate upload session history
                    run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
                    st.session_state["last_upload_run_id"] = run_id

                    progress = st.progress(0)
                    frames_read = 0
                    frames_processed = 0
                    total_violations = 0

                    # Performance optimization configurations
                    FRAME_SKIP = 3  
                    TARGET_SIZE = (640, 360)

                    for i, frame in enumerate(get_frames(temp_video.name)):
                        frames_read += 1

                        # Skip intermediate frames based on performance stride matrix rules
                        if i % FRAME_SKIP != 0:
                            continue

                        frames_processed += 1

                        # Resize frame matrix to optimize speed
                        frame = cv2.resize(frame, TARGET_SIZE)

                        # Inference execution
                        results = yolo_model.predict(
                            source=frame,
                            conf=0.35,
                            verbose=False
                        )
                        result = results[0]

                        tracked = track(result)
                        violations = check(tracked, yolo_model.names)
                        total_violations += len(violations)

                        handle_violations(
                            violations=violations,
                            frame=frame,
                            tracker_instance=tracker,
                            camera="Uploaded Video",
                            zone="Zone A",
                            is_last_frame=False,
                            run_id=run_id,
                        )

                        if frames_read % 10 == 0:
                            progress.progress(min(frames_read / total_video_frames, 1.0))

                    # Flush structural tracker remnants at video boundary termination
                    handle_violations(
                        violations=[],
                        frame=None,
                        tracker_instance=tracker,
                        camera="Uploaded Video",
                        zone="Zone A",
                        is_last_frame=True,
                        run_id=run_id,
                    )

                    progress.progress(1.0)
                    st.success(
                        f"✅ Video Processed Successfully\n\n"
                        f"Total Stream Frames Read: {frames_read}\n\n"
                        f"Active Inference Targets Processed: {frames_processed}\n\n"
                        f"Violations Found: {total_violations}"
                    )
                    processing_succeeded = True

                except Exception as e:
                    st.exception(e)

                if processing_succeeded:
                    st.rerun()

    if mode == "Registered Cameras":
        if st.button(
            "🚀 Run All Registered Cameras",
            type="primary",
            use_container_width=True,
        ):
            progress_placeholder = st.empty()

            def update_progress(camera_name):
                progress_placeholder.success(f"✅ Finished processing {camera_name}")

            with st.spinner("Processing all registered cameras..."):
                # Track multi-camera batch run states as a distinct transactional identity string
                registered_run_id = f"REG_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
                st.session_state["last_upload_run_id"] = registered_run_id
                
                run_all_cameras(progress_callback=update_progress, run_id=registered_run_id)

            st.success("🎉 All cameras processed successfully!")
            st.rerun()

# ==========================================================
# RIGHT PANEL - AI COPILOT
# ==========================================================
with right_col:
    st.header("🤖 SmartFactory AI Copilot")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Safe evaluation context to retrieve fresh stats for dynamically injected layouts
    current_system_stats = get_stats()

    # Render conversational chat interface safely pulling database data fields dynamically
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "📊 Factory Dashboard" in msg["content"]:
                st.markdown("### 📈 Live Telemetry Visualizations (Cached View)")
                
                # Transform db query metrics dynamically to match graph structures
                by_type_list = current_system_stats.get("by_type", [])
                chart_mapping = {item[0]: item[1] for item in by_type_list} if by_type_list else {"No Active Violations": 0}
                st.bar_chart(chart_mapping, horizontal=True)

    prompt = st.chat_input(
        "Ask about incidents, PPE violations or specific cameras..."
    )

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if "real time grid" in prompt.lower():
                response = "🌐 Displaying the Factory Real-Time Status Grid below."
                st.markdown(response)
                st.markdown("### 🌐 Factory Real-Time Status Grid")
            else:
                with st.spinner("Thinking..."):
                    try:
                        response = ask(prompt)
                    except Exception as e:
                        response = f"❌ {e}"

            # ----------------------------------------------------------
            # PDF Interceptor Route Path Handler
            # ----------------------------------------------------------
            if isinstance(response, str) and response.endswith('.pdf') and os.path.exists(response):
                st.success("📄 Executive summary safety report successfully generated!")

                with open(response, "rb") as f:
                    pdf_data = f.read()

                st.download_button(
                    label="📥 Download & Open Safety Brief",
                    data=pdf_data,
                    file_name=os.path.basename(response),
                    mime="application/pdf",
                    use_container_width=True
                )

            # ----------------------------------------------------------
            # Telemetry / Dashboard Route Handler (Dynamic Integration)
            # ----------------------------------------------------------
            elif isinstance(response, str) and "📊 Factory Dashboard" in response:
                st.markdown(response)
                st.markdown("### 📈 Live Telemetry Visualizations")

                # Bind exact live statistical properties straight from get_stats() payload mapping array
                live_total = current_system_stats.get("total", 0)
                live_today = current_system_stats.get("today", 0)
                live_active = current_system_stats.get("active", 0)

                mc1, mc2, mc3 = st.columns(3)
                mc1.metric(label="Total Logged Incidents", value=str(live_total))
                mc2.metric(label="Today's Active Alerts", value=str(live_today))
                mc3.metric(label="Open Unresolved Risks", value=str(live_active))

                st.markdown("#### Structural Violations by Event Type")
                by_type_list = current_system_stats.get("by_type", [])
                type_chart_data = {item[0]: item[1] for item in by_type_list} if by_type_list else {"No Incidents Logged": 0}
                st.bar_chart(type_chart_data, horizontal=True)

                st.markdown("#### High-Density Incident Distribution by Factory Zone")
                by_zone_list = current_system_stats.get("by_zone", [])
                zone_chart_data = {item[0]: item[1] for item in by_zone_list} if by_zone_list else {"No Active Zones": 0}
                st.bar_chart(zone_chart_data)

            # Standard Text response fallback
            else:
                st.markdown(response)

        # Log appropriate text metadata back into persistent session memory arrays
        if isinstance(response, str) and response.endswith(".pdf"):
            st.session_state.messages.append({
                "role": "assistant",
                "content": "📄 Executive Safety Report generated successfully. Use the download button above."
            })
        else:
            st.session_state.messages.append({"role": "assistant", "content": response})

# ==========================================================
# FOOTER ANALYTICS
# ==========================================================
st.markdown("---")
st.header("📊 Factory Safety Analytics")

try:
    stats = get_stats()
    total = stats.get("total", 0)
    today = stats.get("today", 0)
    active = stats.get("active", 0)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Incidents", total)
    c2.metric("Today's Incidents", today)
    c3.metric("Active Violations", active)

    graph_col, camera_col = st.columns([2, 1])

    with graph_col:
        zone_data = pd.DataFrame(stats.get("by_zone", []), columns=["Zone", "Violations"])
        if not zone_data.empty:
            fig = px.bar(zone_data, x="Zone", y="Violations", color="Violations", title="Violations by Zone")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No regional zone data available.")

    with camera_col:
        st.subheader("📷 Violations by Camera")
        with get_connection() as conn:
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            camera_rows = conn.execute(
                """
                SELECT COALESCE(NULLIF(camera, ''), 'Unknown Camera') AS camera, COUNT(*) AS total 
                FROM events 
                GROUP BY camera 
                ORDER BY total DESC
                """
            ).fetchall()

        if camera_rows:
            if len(camera_rows) <= 4:
                for row in camera_rows:
                    st.metric(label=row["camera"], value=f"{row['total']} incidents")
            else:
                camera_df = pd.DataFrame(camera_rows)
                camera_df.columns = ["Camera Source", "Total Violations"]
                st.dataframe(camera_df, use_container_width=True, hide_index=True)
        else:
            st.info("No data yet — run detection first.")

    # ------------------------------------------------------------
    # Current Upload Run Isolation Indicator View
    # ------------------------------------------------------------
    last_run_id = st.session_state.get("last_upload_run_id")
    if last_run_id:
        st.markdown("---")
        with get_connection() as conn:
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            run_rows = conn.execute(
                "SELECT COUNT(*) AS total FROM events WHERE run_id = ?",
                (last_run_id,)
            ).fetchall()
        run_total = run_rows[0]["total"] if run_rows else 0
        st.metric(label=f"🆕 Incidents in This Active Session (Run: {last_run_id})", value=f"{run_total} records")

except Exception as e:
    st.error(f"Analytics Error: {e}")

# ==========================================================
# PDF REPORT EXPORT SECTION
# ==========================================================
st.markdown("---")
st.header("📄 Executive Safety Report Generation")

if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

report_all_time = st.checkbox("Cover all time data metrics", value=True)
date_col1, date_col2 = st.columns(2)

with date_col1:
    report_start_date = st.date_input("Start date", value=date.today() - timedelta(days=30), disabled=report_all_time)
with date_col2:
    report_end_date = st.date_input("End date", value=date.today(), disabled=report_all_time)

if st.button("Generate Executive PDF Report", use_container_width=True):
    try:
        with st.spinner("Generating Executive Report..."):
            start_date = "all time" if report_all_time else report_start_date.isoformat()
            end_date = date.today().isoformat() if report_all_time else report_end_date.isoformat()

            pdf_path = generate_pdf_report(stats=stats, start_date=start_date, end_date=end_date)
            with open(pdf_path, "rb") as f:
                st.session_state.pdf_bytes = f.read()
            st.success("✅ Report generated successfully!")
    except Exception as e:
        st.error(f"Report Generation Error: {e}")

if st.session_state.pdf_bytes is not None:
    st.download_button(
        label="📥 Download Executive Safety Report",
        data=st.session_state.pdf_bytes,
        file_name="SmartFactory_Safety_Report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )