import os
from datetime import date
from fpdf import FPDF
from agents.report_writer import write_incident_summary

# Get the absolute path of the project root directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

def _sanitize_for_pdf(text):
    """fpdf's core Helvetica font only supports latin-1. The AI-written
    summary is new, unpredictable text, and LLMs commonly reach for
    smart quotes/em-dashes that aren't in that range - which throws a
    hard error mid-report instead of just looking slightly off. Normalize
    the common cases and fall back to stripping anything else."""
    if not text:
        return ""
    replacements = {
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-",
        "\u2026": "...",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _draw_table(pdf, title, rows, col_labels=("Category", "Count")):
    """Small helper used for both the by-type and by-zone breakdown tables."""
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, _sanitize_for_pdf(title))
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(120, 7, col_labels[0], border=1)
    pdf.cell(40, 7, col_labels[1], border=1)
    pdf.ln(7)

    pdf.set_font("Helvetica", "", 10)
    if rows:
        for label, count in rows:
            pdf.cell(120, 7, _sanitize_for_pdf(str(label)), border=1)
            pdf.cell(40, 7, str(count), border=1)
            pdf.ln(7)
    else:
        pdf.cell(160, 7, "No data available", border=1)
        pdf.ln(7)

    pdf.ln(6)


def generate_pdf_report(stats, start_date=None, end_date=None, path=None):
    """Build the executive safety PDF report.

    start_date / end_date scope the AI-written narrative summary at the
    top of the report. Defaults to "all time" if not given.
    """
    # Enforce absolute path targeting to prevent Streamlit environment drift
    if path is None:
        path = os.path.join(PROJECT_ROOT, "reports", "safety_report.pdf")
    else:
        path = os.path.abspath(path)

    if start_date is None:
        start_date = "all time"
    if end_date is None:
        end_date = date.today().isoformat()

    # --- ROBUST API FALLBACK IMPLEMENTATION ---
    try:
        summary_text = _sanitize_for_pdf(
            write_incident_summary(start_date, end_date)
        )
    except Exception as e:
        print(f"AI Summary Error: {e}")
        
        # Keep the report generation alive with an explicit metrics backup summary
        summary_text = (
            "AI-generated incident summary is currently unavailable because "
            "the language model quota has been exceeded.\n\n"
            f"Reporting Period: {start_date} to {end_date}\n\n"
            f"Total Incidents: {stats.get('total', 0)}\n"
            f"Today's Incidents: {stats.get('today', 0)}\n"
            f"Active Violations: {stats.get('active', 0)}\n\n"
            "Please review the detailed statistics and violation tables below."
        )
        summary_text = _sanitize_for_pdf(summary_text)

    pdf = FPDF()
    pdf.add_page()

    # ---- Header --------------------------------------------------------
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "SmartFactory Executive Safety Report")
    pdf.ln(12)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Period: {start_date} to {end_date}")
    pdf.ln(6)
    pdf.cell(0, 6, f"Generated: {date.today().isoformat()}")
    pdf.ln(10)

    # ---- Top-line metrics ------------------------------------------------
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Summary Metrics")
    pdf.ln(9)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Total Incidents: {stats.get('total', 0)}")
    pdf.ln(7)
    pdf.cell(0, 7, f"Today's Incidents: {stats.get('today', 0)}")
    pdf.ln(7)
    pdf.cell(0, 7, f"Active Violations: {stats.get('active', 0)}")
    pdf.ln(10)

    # ---- Narrative summary section ----------------------------------------
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Incident Summary")
    pdf.ln(9)

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 7, summary_text)
    pdf.ln(5)

    # ---- Breakdown tables -------------------------------------------------
    _draw_table(pdf, "Violations by Type", stats.get("by_type", []), ("Violation Type", "Count"))
    _draw_table(pdf, "Violations by Zone", stats.get("by_zone", []), ("Zone", "Count"))

    # Ensure the directory tree structures exist prior to output compilation
    os.makedirs(os.path.dirname(path), exist_ok=True)
        
    # Compile the file out to disk
    pdf.output(path)

    # Return the absolute path explicitly to app.py
    return os.path.abspath(path)