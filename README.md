# SmartFactory Copilot

**AI-powered CCTV safety monitoring for factories** — a computer-vision pipeline that detects PPE violations in real time, an agentic AI assistant that can answer questions about the data, and a Streamlit dashboard that ties it all together.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)
![YOLOv8](https://img.shields.io/badge/CV-YOLOv8-purple)
![LangGraph](https://img.shields.io/badge/Agent-LangGraph-1C3C3C)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

**🔗 Live app:** [your-app-name.streamlit.app](https://smartfactory-cctv-ai-copilot-kifg2sg9vh4raur9bbsokh.streamlit.app/) *(replace with your deployed Streamlit URL)*

![Dashboard Preview](assets/screenshot.png)
*(Swap in a real screenshot or short GIF of your running dashboard at `assets/screenshot.png` — a visual first impression goes a long way with recruiters and reviewers.)*

---

## Overview

SmartFactory Copilot watches CCTV footage the way a safety officer would — continuously, and without getting tired. It runs a fine-tuned YOLOv8 model over uploaded video, flags workers missing a hardhat or safety vest, and automatically logs every violation as a structured incident with a timestamped snapshot as proof.

On top of that detection layer sits an **agentic AI safety assistant**: instead of answering from one fixed prompt, it decides for itself whether a question needs an exact database lookup, a semantic search, or a stats summary — and can chain multiple lookups together to answer comparison questions like *"is this week better or worse than last week?"* Everything is surfaced through a single Streamlit dashboard: upload footage, watch live metrics update, chat with the assistant, and download a one-click PDF safety report.

The project started as a 4-day guided build, then went through a second pass to fix correctness bugs, fine-tune the detection model on real data, deepen the agent's reasoning, and add multi-camera support. See [Known Limitations](#known-limitations) for an honest account of what's simplified and what isn't.

## Key Features

- **🦺 PPE violation detection** — a fine-tuned YOLOv8 model flags missing hardhats and safety vests frame by frame, filtering out any detection the model is less than 50% confident about.
- **🔁 Persistent worker tracking** — ByteTrack (via `supervision`) assigns a consistent ID to each worker across frames instead of re-detecting them from scratch.
- **🧩 Incident deduplication** — a continuous violation (e.g., 10 seconds without a hardhat, ~300 frames) collapses into **one** incident with a start time, end time, and duration — not hundreds of duplicate rows.
- **📸 Automatic snapshot evidence** — every incident is saved with a timestamped image as visual proof.
- **🗃️ Dual-database storage** — SQLite for exact, structured queries (counts, filters by zone/date/type) and ChromaDB for semantic, natural-language search — both filled automatically by the same detection pipeline.
- **🤖 Agentic safety assistant** — a LangGraph tool-calling agent (`create_react_agent`, Gemini-backed) that picks the right tool per question, chains multiple tool calls for multi-step questions, and remembers earlier turns in the same conversation via a memory checkpointer.
- **📝 AI-written incident reports** — a second, narrowly-scoped agent turns raw incident data into a plain-English prose summary, combined into a downloadable PDF alongside structured breakdowns by type and zone.
- **📈 Live dashboard** — upload footage, watch a progress bar, and see live totals, a violations-by-zone chart, and a per-camera breakdown.
- **🎥 Multi-camera support** — cameras are real rows in a database (name, zone, source), looped over dynamically, each with its own independent violation tracker.
- **⚡ Non-blocking processing** — detection runs in a background thread with an auto-refreshing status indicator, so the dashboard never freezes mid-run.

## How It Works

The system is built around five core components:

| Block | Role | Key files |
|---|---|---|
| 👁️ **The Eyes** | A YOLOv8 model — fine-tuned from a pretrained PPE checkpoint — scans each frame and draws boxes around people, hardhats, vests, masks, and more. | `models/detector.py` |
| 📖 **The Rulebook** | Confidence-filtered logic decides which boxes count as a real violation, and a per-worker tracker collapses a multi-frame violation into a single incident. | `cctv/safety_engine.py`, `cctv/violation_tracker.py` |
| 🗄️ **The Filing Cabinet** | SQLite for exact structured records; ChromaDB for meaning-based semantic search. Both populated automatically, in parallel, by the same pipeline. | `database/db.py`, `rag/ingest.py` |
| 🤖 **The Assistant** | A LangGraph agent that decides which tool to call — SQL lookup, semantic search, or stats — and can call more than one per question, with conversation memory. | `agents/copilot.py`, `agents/tools.py` |
| 📊 **The Dashboard** | A Streamlit page tying it all together — upload, live metrics, charts, chat, and PDF export. | `app.py` |

**Processing pipeline, end to end:**

```
Video frame → YOLOv8 detection → ByteTrack (worker ID) → confidence filter
    → violation rule-check → deduplication (ViolationTracker)
    → [snapshot saved] + [SQLite row] + [ChromaDB entry] → Dashboard / Agent
```

## Model Evaluation — Day 6 Fine-Tuning Results

The PPE detection model was fine-tuned from the pretrained checkpoint using Ultralytics YOLOv8, then evaluated on a held-out test split. Final results:

| Metric | Value |
|---|---|
| Precision (Box(P)) | 0.589 |
| Recall (R) | 0.475 |
| mAP50 | 0.488 |

**Notes:**
- Highly accurate at detecting **Hardhats** (0.872 Precision)
- Excellent at catching **Masks** (0.81 Recall)

*Precision measures how often a flagged violation was actually correct; recall measures how many of the real violations in the test set were actually caught; mAP50 is the standard mean-average-precision score at 50% IoU used to summarize overall detection quality.*

> Add a baseline (pre-fine-tuning) row here for a full before/after comparison — see Day 6 of the Enhancement Guide for the exact `model.val()` steps used to produce these numbers.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Computer vision | YOLOv8 (Ultralytics), OpenCV, `supervision` (ByteTrack) |
| Structured storage | SQLite |
| Semantic storage | ChromaDB (`PersistentClient`) |
| Agentic AI | LangChain, LangGraph (`create_react_agent`, `MemorySaver`), Google Gemini (`langchain-google-genai`) |
| Dashboard | Streamlit, Plotly, `streamlit-autorefresh` |
| Reporting | fpdf2 |
| Training / dataset | Roboflow (Construction Site Safety dataset), Google Colab (T4 GPU) |

## Project Structure

```text
smartfactory_copilot/
├── app.py                      # Streamlit dashboard (entry point)
├── config.py                   # Loads GEMINI_API_KEY from .env / st.secrets
├── requirements.txt
├── .env                        # Local secrets — never committed
├── README.md
├── data/
│   ├── factory.mp4             # Camera 1 test footage
│   ├── factory2.mp4            # Camera 2 test footage (multi-camera)
│   └── sample.jpg
├── database/
│   ├── db.py                   # SQLite schema, connections, queries
│   ├── factory.db              # Generated at runtime
│   └── chroma/                 # ChromaDB persistent vector store
├── models/
│   ├── detector.py             # Cached YOLOv8 model loading + inference
│   ├── best.pt                 # Original pretrained PPE weights
│   └── best_finetuned.pt       # Fine-tuned weights (Day 6)
├── cctv/
│   ├── stream.py                # Frame-by-frame video reader
│   ├── tracker.py                # ByteTrack worker tracking
│   ├── safety_engine.py          # Violation rules + confidence filter
│   ├── violation_tracker.py      # Deduplicates violations into incidents
│   ├── snapshot.py               # Saves proof images per incident
│   ├── incident_pipeline.py      # Wires detection → storage → RAG
│   └── multi_camera_runner.py    # Loops detection across active cameras
├── rag/
│   └── ingest.py                 # ChromaDB ingestion for semantic search
├── agents/
│   ├── tools.py                  # SQL lookup / semantic search / stats tools
│   ├── copilot.py                # Main LangGraph agent (memory-enabled)
│   └── report_writer.py          # Secondary agent for prose report summaries
├── reports/
│   ├── generate_report.py        # PDF safety report builder
│   └── safety_report.pdf         # Generated on demand
├── scripts/
│   └── setup_cameras.py          # One-time camera registration
├── assets/
│   └── incidents/                # Snapshot images (violation proof)
└── tests/
    ├── test_detection.py
    ├── test_rag.py
    └── test_agent.py
```

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- A free [Google Gemini API key](https://aistudio.google.com)
- (Optional, for retraining) A free [Roboflow](https://roboflow.com) account and access to [Google Colab](https://colab.research.google.com)

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/smartfactory_copilot.git
cd smartfactory_copilot
```

### 2. Set up a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add the detection model weights

Model weights aren't committed to this repo (they're large binary files — see the note in the deployment section below). Download `best.pt` from the [Construction Site Safety project on Roboflow](https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety) (or use your own fine-tuned `best_finetuned.pt`) and place it inside `models/`.

### 5. Configure environment variables

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_actual_key_here
```

Get a free key at [aistudio.google.com](https://aistudio.google.com). **Never commit `.env` to GitHub** — add it to `.gitignore`.

### 6. (Optional) Register cameras for multi-camera mode

```bash
python scripts/setup_cameras.py
```

### 7. Run it

```bash
streamlit run app.py
```

The dashboard opens automatically at `http://localhost:8501`.

<details>
<summary><strong>Suggested <code>.gitignore</code></strong></summary>

```
# Secrets
.env
.streamlit/secrets.toml

# Virtual environment
venv/

# Python
__pycache__/
*.pyc

# Runtime-generated data
database/factory.db
database/chroma/
assets/incidents/
reports/safety_report.pdf

# Large model weights (download manually — see Step 4 in Getting Started)
models/*.pt
models/*.onnx
```

</details>

## Deploying on Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in, and click **New app**.
3. Select your repo and branch, and set the main file path to `app.py`.
4. Before deploying, open **Advanced settings** and paste your key in TOML format:
   ```toml
   GEMINI_API_KEY = "your_actual_key_here"
   ```
5. Click **Deploy**. Your app gets a live URL like `https://<your-app-name>.streamlit.app`.
6. Need to change a key later? Go to your app's settings from your [share.streamlit.io](https://share.streamlit.io) workspace → **Secrets** — it updates without a redeploy.

Since `config.py` currently reads only from `.env` via `python-dotenv`, add a small fallback so the same code works both locally and on Community Cloud:

```python
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
```

**A note on file size:** GitHub blocks pushes over 100MB per file. If `best.pt` / `best_finetuned.pt` or your sample videos are large, use [Git LFS](https://git-lfs.com/) or host them elsewhere (a GitHub Release asset, cloud storage bucket) and download them at startup instead of committing them directly.

## Usage

1. **Upload footage** — drop an `.mp4` file into the uploader and click **Run Detection**.
2. **Watch live stats** — total violations, violation types, and zones affected update as soon as processing finishes.
3. **Check the zone / camera breakdown** — a Plotly bar chart and a per-camera list show where violations are concentrated.
4. **Ask the assistant** anything about the data, for example:
   - *"How many total violations were detected?"*
   - *"Which zone has the most violations?"*
   - *"Compare the number of violations in the last 7 days versus the 7 days before that — is it getting better or worse?"*
   - *"How many violations happened in Zone A?"* → *"What about Zone B?"* (follow-up questions work — the agent remembers context)
5. **Generate a report** — click **Generate PDF Safety Report** for an AI-written summary plus a structured breakdown, ready to download.

## Known Limitations

Being upfront about what's simplified is part of what makes the rest of the project credible:

- **Threading ≠ true parallelism.** Background processing keeps the dashboard responsive, but Python's Global Interpreter Lock means it doesn't give CPU-heavy YOLO inference a real parallel speed boost. A production system would use multiprocessing or separate worker machines for that.
- **Cameras are local video files, not live feeds.** The `cameras` table is designed to scale to many sources, but currently points at local `.mp4` files rather than real RTSP network streams.
- **SQLite, not Postgres.** Fine for a single-user demo; a real multi-camera, multi-user deployment would want a database built for concurrent writes.
- **The detection model is fine-tuned, not trained from scratch.** It started from a pretrained checkpoint on the Roboflow Construction Site Safety dataset.
- **The "heatmap" is zone-level, not pixel-level.** It's a color-scaled bar chart by zone, not a true spatial heatmap overlaid on camera footage.
- **Role-based login and predictive maintenance are not implemented**, despite appearing in early project notes.

## Roadmap

- [ ] Baseline (pre-fine-tuning) metrics alongside the current results for a full before/after comparison
- [ ] Real RTSP camera ingestion instead of local video files
- [ ] Migrate from SQLite to Postgres for concurrent multi-user writes
- [ ] True parallel processing across cameras via multiprocessing / separate workers
- [ ] Pixel-coordinate heatmap overlay on camera footage
- [ ] Role-based login (Manager / Admin / Safety Officer)
- [ ] Date-range picker in the dashboard for custom PDF report windows

## Acknowledgments

- [Roboflow](https://roboflow.com) and the [Construction Site Safety](https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety) dataset/project for the base PPE detection dataset and pretrained weights
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [LangChain / LangGraph](https://www.langchain.com/langgraph) and [Google Gemini](https://ai.google.dev/) for the agentic assistant
- [Pexels](https://www.pexels.com/) and [Pixabay](https://pixabay.com/) for free, license-friendly test footage

## Contributing

This started as a personal learning project, but issues and pull requests are welcome if you spot a bug or have an idea worth adding.

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details. *(Add a `LICENSE` file with your preferred license, or update this section to match.)*

---

<p align="center"><sub>Built as a hands-on project in applied computer vision and agentic AI.</sub></p>
