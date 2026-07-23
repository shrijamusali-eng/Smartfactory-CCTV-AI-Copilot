"""
PDF report generation for SmartFactory CCTV Safety Monitor.

I don't have your actual Day 4 version of this file (it wasn't part of what
you uploaded), so the scaffolding below - fonts, page setup, table layout -
is a reasonable reconstruction based on the fpdf calls shown in the Day 5
instructions (pdf.set_font / pdf.cell / pdf.multi_cell) and the stats shape
already used in app.py (stats["by_zone"] etc). If your real Day 4 file has
different styling, a logo, different helper names, etc., keep that file and
just port over the three highlighted pieces:
  1. `from agents.report_writer import write_incident_summary`
  2. the `summary_text = write_incident_summary(start_date, end_date)` call
  3. the `pdf.multi_cell(0, 7, summary_text)` block right after it

Assumes get_stats() returns a dict shaped like:
    {
        "total": int,
        "today": int,
        "active": int,
        "by_zone": [(zone_name, count), ...],
        "by_type": [(violation_type, count), ...],
    }
`by_zone` is confirmed by app.py's chart code. `by_type` is assumed, to
match the "existing by-type ... sections" mentioned in the Day 5 notes -
adjust the key name in _draw_table's calls below if yours differs.
"""

import os
from datetime import date

from fpdf import FPDF

from agents.report_writer import write_incident_summary


def _sanitize_for_pdf(text):
    """fpdf's core Helvetica font only supports latin-1. The AI-written
    summary is new, unpredictable text, and LLMs commonly reach for
    smart quotes/em-dashes that aren't in that range - which throws a
    hard error mid-report instead of just looking slightly off. Normalize
    the common cases and fall back to stripping anything else."""
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


def generate_pdf_report(stats, start_date=None, end_date=None, path="reports/safety_report.pdf"):
    """Build the executive safety PDF report.

    start_date / end_date scope the AI-written narrative summary at the
    top of the report. Defaults to "all time" if not given, so existing
    callers that only pass `stats` keep working.
    """
    if start_date is None:
        start_date = "all time"
    if end_date is None:
        end_date = date.today().isoformat()

    summary_text = _sanitize_for_pdf(write_incident_summary(start_date, end_date))

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

    # ---- AI-written narrative summary (new in Day 5) ----------------------
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Incident Summary")
    pdf.ln(9)

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 7, summary_text)
    pdf.ln(5)

    # ---- Breakdown tables (same structure as Day 4) -----------------------
    _draw_table(pdf, "Violations by Type", stats.get("by_type", []), ("Violation Type", "Count"))
    _draw_table(pdf, "Violations by Zone", stats.get("by_zone", []), ("Zone", "Count"))

    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    pdf.output(path)

    return path