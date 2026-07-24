import sys
import os
import tempfile
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

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
# Initialize Database
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
                    # Leverage streaming and tracking pipeline layers safely
                    from cctv.stream import get_frames
                    from cctv.tracker import track

                    # Safely load weights only when explicitly requested
                    yolo_model = get_model()

                    tracker = ViolationTracker(
                        timeout_seconds=3
                    )

                    progress = st.progress(0)
                    frame_count = 0
                    total_violations = 0

                    for frame in get_frames(temp_video.name):
                        frame_count += 1

                        # YOLO Prediction via lazy-loaded instance
                        results = yolo_model.predict(
                            source=frame,
                            conf=0.35,
                            verbose=False
                        )
                        result = results[0]

                        print("\n" + "=" * 80)
                        print(f"FRAME: {frame_count}")
                        print("YOLO Boxes:", len(result.boxes))

                        if len(result.boxes):
                            detected_labels = [
                                yolo_model.names[int(cls)]
                                for cls in result.boxes.cls
                            ]
                            print("Detected Labels :", detected_labels)
                            print("Confidence      :", result.boxes.conf.tolist())
                        else:
                            print("❌ No detections from YOLO")
                        print("=" * 80)

                        # Tracking Analysis
                        tracked = track(result)
                        print("Tracked Object Count:", len(tracked))

                        # Safety Violation Engine Parsing
                        violations = check(
                            tracked,
                            yolo_model.names,
                        )
                        print("Violations Found:", len(violations))
                        total_violations += len(violations)

                        # Save incident frames via data pipeline layer
                        handle_violations(
                            violations=violations,
                            frame=frame,
                            tracker_instance=tracker,
                            camera="Uploaded Video",
                            zone="Zone A",
                            is_last_frame=False,
                        )

                        if frame_count % 10 == 0:
                            progress.progress(
                                min(frame_count / 500, 1.0)
                            )

                    # Flush lagging buffer sequences out of memory
                    handle_violations(
                        violations=[],
                        frame=None,
                        tracker_instance=tracker,
                        camera="Uploaded Video",
                        zone="Zone A",
                        is_last_frame=True,
                    )

                    progress.progress(1.0)

                    st.success(
                        f"✅ Video Processed Successfully\n\n"
                        f"Frames Processed: {frame_count}\n\n"
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
                progress_placeholder.success(
                    f"✅ Finished processing {camera_name}"
                )

            with st.spinner("Processing all registered cameras..."):
                run_all_cameras(
                    progress_callback=update_progress
                )

            st.success("🎉 All cameras processed successfully!")
            st.rerun()

# ==========================================================
# RIGHT PANEL - AI COPILOT
# ==========================================================
with right_col:

    st.header("🤖 SmartFactory AI Copilot")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input(
        "Ask about incidents, PPE violations or specific cameras (e.g., 'Show incidents from Camera 1')..."
    )

    if prompt:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = ask(prompt)
                except Exception as e:
                    response = f"❌ {e}"

                st.markdown(response)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response,
            }
        )

# ==========================================================
# ANALYTICS
# ==========================================================
st.markdown("---")
st.header("📊 Factory Safety Analytics")

try:
    stats = get_stats()

    total = stats.get("total", 0)
    today = stats.get("today", 0)
    active = stats.get("active", 0)

    # Global Metrics Row
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Incidents", total)
    c2.metric("Today's Incidents", today)
    c3.metric("Active Violations", active)

    # Breakdown Split: Chart Left, Camera Data Right
    graph_col, camera_col = st.columns([2, 1])

    with graph_col:
        zone_data = pd.DataFrame(
            stats.get("by_zone", []),
            columns=["Zone", "Violations"],
        )

        if not zone_data.empty:
            fig = px.bar(
                zone_data,
                x="Zone",
                y="Violations",
                color="Violations",
                title="Violations by Zone",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No regional zone data available.")

    with camera_col:
        st.subheader("📷 Violations by Camera")
        with get_connection() as conn:
            # Enforce row factory mappings or dict bindings explicitly
            conn.row_factory = lambda cursor, row: {
                col[0]: row[idx] for idx, col in enumerate(cursor.description)
            }
            camera_rows = conn.execute(
                """
                SELECT
                    COALESCE(NULLIF(camera, ''), 'Unknown Camera') AS camera,
                    COUNT(*) AS total
                FROM events
                GROUP BY camera
                ORDER BY total DESC
                """
            ).fetchall()

        # Display camera statistics
        if camera_rows:
            if len(camera_rows) <= 4:
                for row in camera_rows:
                    st.metric(
                        label=row["camera"],
                        value=f"{row['total']} incidents"
                    )
            else:
                camera_df = pd.DataFrame(camera_rows)
                camera_df.columns = ["Camera Source", "Total Violations"]
                st.dataframe(camera_df, use_container_width=True, hide_index=True)
        else:
            st.info("No data yet — run detection first.")

except Exception as e:
    st.error(f"Analytics Error: {e}")

# ==========================================================
# PDF REPORT
# ==========================================================
st.markdown("---")
st.header("📄 Executive Safety Report")

# Keep generated PDF across Streamlit reruns
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

report_all_time = st.checkbox(
    "Cover all time",
    value=True,
    help="Uncheck to generate the report for a custom date range.",
)

date_col1, date_col2 = st.columns(2)

with date_col1:
    report_start_date = st.date_input(
        "Start date",
        value=date.today() - timedelta(days=30),
        disabled=report_all_time,
    )

with date_col2:
    report_end_date = st.date_input(
        "End date",
        value=date.today(),
        disabled=report_all_time,
    )

if st.button(
    "Generate Executive PDF Report",
    use_container_width=True,
):
    try:
        with st.spinner("Generating Executive Report..."):

            if report_all_time:
                start_date = "all time"
                end_date = date.today().isoformat()
            else:
                start_date = report_start_date.isoformat()
                end_date = report_end_date.isoformat()

            # Receives the explicit absolute path back from the engine
            pdf_path = generate_pdf_report(
                stats=stats,
                start_date=start_date,
                end_date=end_date,
            )

            # Read the generated PDF into memory safely
            with open(pdf_path, "rb") as f:
                st.session_state.pdf_bytes = f.read()

            st.success("✅ Report generated successfully!")

    except Exception as e:
        st.error(f"Report Generation Error: {e}")

# Always show the download button after generation
if st.session_state.pdf_bytes is not None:
    st.download_button(
        label="📥 Download Executive Safety Report",
        data=st.session_state.pdf_bytes,
        file_name="SmartFactory_Safety_Report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )