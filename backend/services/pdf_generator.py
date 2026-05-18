from __future__ import annotations

from io import BytesIO
from pathlib import Path

import matplotlib
from matplotlib import pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.utils import first_name


matplotlib.use("Agg")


def _build_chart(sessions: list[object]) -> BytesIO:
    figure, axis = plt.subplots(figsize=(8, 3))
    ordered = list(reversed(sessions[-30:]))
    dates = [session.recorded_at.strftime("%m-%d") for session in ordered]
    scores = [session.composite_risk_score for session in ordered]
    axis.plot(dates, scores, color="#0f766e", linewidth=2, marker="o", markersize=4)
    axis.set_title("Composite Risk Trend")
    axis.set_ylim(0, 100)
    axis.tick_params(axis="x", rotation=45)
    axis.grid(alpha=0.2)
    figure.tight_layout()

    buffer = BytesIO()
    figure.savefig(buffer, format="png", dpi=160)
    plt.close(figure)
    buffer.seek(0)
    return buffer


def generate_patient_report_pdf(
    patient: object,
    sessions: list[object],
    weekly_summary: str,
    correlation_findings: list[str] | None = None,
) -> bytes:
    styles = getSampleStyleSheet()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=f"VoiceTrace Report - {patient.name}")
    story = []

    story.append(Paragraph(f"VoiceTrace Report for {patient.name}", styles["Title"]))
    story.append(
        Paragraph(
            f"Caregiver: {patient.caregiver_name} ({patient.caregiver_relationship})<br/>"
            f"Location: {patient.location}<br/>"
            f"Monitoring since: {patient.created_at:%B %d, %Y}<br/>"
            "For clinical support only. Not a diagnostic tool. Requires physician review.",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 12))

    chart = _build_chart(sessions)
    story.append(Image(chart, width=500, height=190))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Weekly Summary for {first_name(patient.name)}", styles["Heading2"]))
    story.append(Paragraph(weekly_summary, styles["BodyText"]))
    story.append(Spacer(1, 12))

    latest_notes = sessions[0].clinical_notes if sessions else "No session data available."
    latest_insight = sessions[0].caregiver_insight if sessions else "No insight available yet."
    story.append(Paragraph("Latest Clinical Notes", styles["Heading2"]))
    story.append(Paragraph(latest_notes, styles["BodyText"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Narrative Insight", styles["Heading2"]))
    story.append(Paragraph(latest_insight, styles["BodyText"]))
    story.append(Spacer(1, 12))

    if correlation_findings:
        story.append(Paragraph("Life Events & Voice", styles["Heading2"]))
        for finding in correlation_findings[:3]:
            story.append(Paragraph(f"• {finding}", styles["BodyText"]))
        story.append(Spacer(1, 12))

    table_rows = [["Date", "Duration", "Composite", "TTR", "MLU", "Coherence"]]
    for session in sessions[:30]:
        table_rows.append(
            [
                session.recorded_at.strftime("%Y-%m-%d"),
                f"{session.duration_seconds:.0f}s",
                f"{session.composite_risk_score:.1f}",
                f"{session.ttr_score:.2f}",
                f"{session.mlu_score:.2f}",
                f"{session.semantic_coherence:.1f}",
            ]
        )
    table = Table(table_rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.append(Paragraph("Recent Sessions", styles["Heading2"]))
    story.append(table)

    doc.build(story)
    return buffer.getvalue()
