# ==========================================================
# services/report_service.py (or equivalent service module)
# ==========================================================
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class ReportService:
    """Manages document serialization and exports safety logs directly into presentation-ready PDFs."""

    def compile_markdown_to_pdf(self, report_markdown: str, filename: str = "safety_brief.pdf") -> str:
        """Builds structured tabular page layouts and returns the absolute PDF file path on success."""
        try:
            output_dir = os.path.join(os.getcwd(), "outputs")
            os.makedirs(output_dir, exist_ok=True)
            pdf_path = os.path.join(output_dir, filename)

            doc = SimpleDocTemplate(
                pdf_path, pagesize=letter, 
                rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
            )
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'DocTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor("#1E293B"), spaceAfter=12
            )
            body_style = ParagraphStyle(
                'DocBody', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor("#334155"), spaceAfter=8
            )

            for line in report_markdown.split('\n'):
                cleaned = line.strip()
                if not cleaned:
                    continue
                if cleaned.startswith("## "):
                    story.append(Spacer(1, 8))
                    story.append(Paragraph(cleaned.replace("## ", ""), title_style))
                elif cleaned.startswith("### "):
                    h3_style = ParagraphStyle('H3', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor("#0F172A"), spaceAfter=6)
                    story.append(Paragraph(cleaned.replace("### ", ""), h3_style))
                else:
                    story.append(Paragraph(cleaned.replace("**", ""), body_style))

            doc.build(story)
            return os.path.abspath(pdf_path)
            
        except Exception as e:
            raise RuntimeError(f"Document generation failed: {e}")