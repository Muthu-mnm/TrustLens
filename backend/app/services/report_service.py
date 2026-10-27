import io
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

FOOTER_TEXT = "PROTOTYPE - NOT OFFICIAL AICTE SYSTEM. Advisory only. Human review required."

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
    )
    from reportlab.pdfgen import canvas
    HAVE_REPORTLAB = True
except ImportError:
    HAVE_REPORTLAB = False
    logger.warning("reportlab is not installed. PDF generation will use fallback generator.")


class NumberedCanvas(canvas.Canvas if HAVE_REPORTLAB else object):
    """Two-pass canvas to dynamically compute and draw page count and footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4a5568"))

        # Running header on subsequent pages
        if self._pageNumber > 1:
            self.drawString(36, 762, "TrustLens — AICTE Document Scrutiny Evaluation Report")
            self.setStrokeColor(colors.HexColor("#cbd5e0"))
            self.setLineWidth(0.5)
            self.line(36, 756, 576, 756)

        # Running footer
        self.setStrokeColor(colors.HexColor("#cbd5e0"))
        self.setLineWidth(0.5)
        self.line(36, 38, 576, 38)
        self.drawString(36, 26, FOOTER_TEXT)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 26, page_str)
        self.restoreState()


def _get_val(obj: Any, key: str, default: Any = "") -> Any:
    """Helper to safely extract key from dict or model object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _generate_fallback_pdf(application_id: str) -> bytes:
    """Minimal valid PDF fallback in case ReportLab is not available."""
    content = (
        f"%PDF-1.4\n"
        f"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        f"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        f"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources <<>>>> endobj\n"
        f"4 0 obj <</Length 180>> stream\n"
        f"BT /F1 14 Tf 50 720 Td (TrustLens Document Scrutiny Report - {application_id}) Tj\n"
        f"0 -30 Td /F1 10 Tf ({FOOTER_TEXT}) Tj ET\n"
        f"endstream\n"
        f"endobj\n"
        f"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000216 00000 n \n"
        f"trailer <</Size 5 /Root 1 0 R>>\nstartxref\n440\n%%EOF"
    )
    return content.encode("latin1")


def generate_report(
    application: dict | Any,
    documents: list[dict | Any],
    findings: list[dict | Any],
    extracted_fields: list[dict | Any],
    audit_entries: list[dict | Any]
) -> bytes:
    """
    Generate an evaluation report in PDF format.
    Includes:
    - Cover Header & Disclaimer
    - Section 1: Application Summary
    - Section 2: Extracted Fields
    - Section 3: Findings & Anomalies
    - Section 4: Risk Score & Severity Breakdown
    - Section 5: Audit Trail
    """
    app_id = _get_val(application, "app_id") or _get_val(application, "id") or "APP-UNKNOWN"

    if not HAVE_REPORTLAB:
        return _generate_fallback_pdf(app_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    # Define custom palette
    c_primary = colors.HexColor("#1e3a8a")     # Deep AICTE Blue
    c_secondary = colors.HexColor("#0284c7")   # Bright Blue Accent
    c_dark = colors.HexColor("#1e293b")        # Text Dark
    c_warning = colors.HexColor("#d97706")     # Amber Warning
    c_danger = colors.HexColor("#dc2626")      # Critical Red
    c_light_bg = colors.HexColor("#f8fafc")

    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=c_primary,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "CoverSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=12
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=c_primary,
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=c_dark
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#991b1b")
    )

    story = []

    # -------------------------------------------------------------
    # Header & Cover Title
    # -------------------------------------------------------------
    story.append(Paragraph("TrustLens™ AICTE Scrutiny Engine", title_style))
    gen_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    story.append(Paragraph(f"Application Scrutiny & Explainable Verification Dossier • Generated: {gen_time}", subtitle_style))

    # Prominent Disclaimer Callout Box
    disclaimer_html = (
        "<b>OFFICIAL PROTOTYPE ADVISORY:</b> This scrutiny evaluation report was generated automatically "
        "by the TrustLens Decision-Support MVP for SIH26261. It does NOT constitute an official AICTE sanction "
        "or rejection. All findings, OCR extractions, and risk metrics are advisory and require review "
        "by designated human Scrutiny Officers."
    )
    disclaimer_table = Table([[Paragraph(disclaimer_html, disclaimer_style)]], colWidths=[540])
    disclaimer_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#f87171")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(disclaimer_table)
    story.append(Spacer(1, 14))

    # -------------------------------------------------------------
    # Section 1: Application Summary
    # -------------------------------------------------------------
    story.append(Paragraph("1. Application Summary", section_heading))
    inst_name = _get_val(application, "institution_name", "N/A")
    app_type = _get_val(application, "app_type", "Engineering & Technology")
    status = _get_val(application, "status", "analyzed")
    risk_score = _get_val(application, "risk_score", 0.0)
    trust_score = _get_val(application, "trust_score", round(max(0.0, 100.0 - float(risk_score)), 1))
    risk_band = _get_val(application, "risk_band", "Low")
    doc_count = len(documents)

    summary_data = [
        [
            Paragraph("<b>Application ID:</b>", body_style), Paragraph(str(app_id), body_style),
            Paragraph("<b>Scrutiny Status:</b>", body_style), Paragraph(str(status).upper(), body_style)
        ],
        [
            Paragraph("<b>Institution Name:</b>", body_style), Paragraph(str(inst_name), body_style),
            Paragraph("<b>Program Type:</b>", body_style), Paragraph(str(app_type), body_style)
        ],
        [
            Paragraph("<b>Uploaded Documents:</b>", body_style), Paragraph(f"{doc_count} document(s)", body_style),
            Paragraph("<b>Risk Band / Score:</b>", body_style), Paragraph(f"<b>{risk_band}</b> (Risk: {risk_score}/100, Trust: {trust_score}/100)", body_style)
        ]
    ]

    summary_table = Table(summary_data, colWidths=[110, 160, 110, 160])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_light_bg),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 14))

    # -------------------------------------------------------------
    # Section 2: Extracted Fields
    # -------------------------------------------------------------
    story.append(Paragraph("2. Extracted Application Fields", section_heading))
    if not extracted_fields:
        story.append(Paragraph("<i>No structured fields have been extracted yet.</i>", body_style))
    else:
        fields_data = [
            [
                Paragraph("Field Name", table_header),
                Paragraph("Extracted Value", table_header),
                Paragraph("Confidence", table_header),
                Paragraph("Page", table_header)
            ]
        ]
        for field in extracted_fields[:15]:
            fname = _get_val(field, "field_name")
            fval = _get_val(field, "field_value")
            conf = _get_val(field, "confidence", 1.0)
            pg = _get_val(field, "page_number", 1)

            fields_data.append([
                Paragraph(f"<b>{fname}</b>", body_style),
                Paragraph(str(fval)[:100], body_style),
                Paragraph(f"{float(conf)*100:.0f}%", body_style),
                Paragraph(f"p. {pg}", body_style)
            ])

        fields_table = Table(fields_data, colWidths=[140, 260, 80, 60])
        fields_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_primary),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light_bg]),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(fields_table)
    story.append(Spacer(1, 14))

    # -------------------------------------------------------------
    # Section 3: Findings Table
    # -------------------------------------------------------------
    story.append(Paragraph("3. Scrutiny Findings & Discrepancies", section_heading))
    if not findings:
        story.append(Paragraph("<i>No compliance discrepancies or tampering anomalies detected.</i>", body_style))
    else:
        findings_data = [
            [
                Paragraph("Severity", table_header),
                Paragraph("Finding Title", table_header),
                Paragraph("Type", table_header),
                Paragraph("Evidence / Details", table_header),
                Paragraph("Review Status", table_header)
            ]
        ]
        for f in findings:
            sev = str(_get_val(f, "severity", "medium")).lower()
            title = _get_val(f, "title", "Anomaly")
            ftype = _get_val(f, "finding_type", "compliance")
            evidence = _get_val(f, "evidence", "") or _get_val(f, "description", "")
            rstatus = _get_val(f, "review_status", "pending")

            sev_color = "#dc2626" if sev == "critical" else "#ea580c" if sev == "high" else "#ca8a04" if sev == "medium" else "#2563eb"
            sev_html = f"<font color='{sev_color}'><b>{sev.upper()}</b></font>"

            findings_data.append([
                Paragraph(sev_html, body_style),
                Paragraph(f"<b>{title}</b>", body_style),
                Paragraph(ftype, body_style),
                Paragraph(str(evidence)[:140], body_style),
                Paragraph(f"<b>{rstatus}</b>", body_style)
            ])

        findings_table = Table(findings_data, colWidths=[65, 125, 80, 180, 90])
        findings_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_primary),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light_bg]),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(findings_table)
    story.append(Spacer(1, 14))

    # -------------------------------------------------------------
    # Section 4: Risk Score & Breakdown
    # -------------------------------------------------------------
    story.append(Paragraph("4. Risk Score & Breakdown Analysis", section_heading))
    sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev = str(_get_val(f, "severity", "medium")).lower()
        if sev in sev_counts:
            sev_counts[sev] += 1

    risk_data = [
        [
            Paragraph("Metric", table_header),
            Paragraph("Evaluated Score", table_header),
            Paragraph("Assessment Explanation", table_header)
        ],
        [
            Paragraph("<b>Advisory Risk Score</b>", body_style),
            Paragraph(f"<b>{risk_score}/100</b>", body_style),
            Paragraph("Penalty points aggregated across detected anomalies (0 = Low Risk, 100 = Critical Risk).", body_style)
        ],
        [
            Paragraph("<b>Compliance Trust Score</b>", body_style),
            Paragraph(f"<b>{trust_score}/100</b>", body_style),
            Paragraph("Base 100 compliance metric remaining after penalty deductions.", body_style)
        ],
        [
            Paragraph("<b>Risk Classification</b>", body_style),
            Paragraph(f"<b>{risk_band} Risk</b>", body_style),
            Paragraph(
                f"Findings breakdown: {sev_counts['critical']} Critical, "
                f"{sev_counts['high']} High, {sev_counts['medium']} Medium, "
                f"{sev_counts['low']} Low.",
                body_style
            )
        ]
    ]

    risk_table = Table(risk_data, colWidths=[140, 120, 280])
    risk_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light_bg]),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 14))

    # -------------------------------------------------------------
    # Section 5: Audit Trail
    # -------------------------------------------------------------
    story.append(Paragraph("5. Cryptographic Audit Trail", section_heading))
    if not audit_entries:
        story.append(Paragraph("<i>No audit log entries recorded for this application.</i>", body_style))
    else:
        audit_data = [
            [
                Paragraph("Timestamp (UTC)", table_header),
                Paragraph("Actor", table_header),
                Paragraph("Action", table_header),
                Paragraph("Details & Hash Chain", table_header)
            ]
        ]
        for a in audit_entries[:15]:
            ts = _get_val(a, "timestamp") or _get_val(a, "created_at")
            ts_str = ts.strftime("%Y-%m-%d %H:%M") if isinstance(ts, datetime) else str(ts)[:16]
            actor = _get_val(a, "actor", "System")
            action = _get_val(a, "action", "Action")
            details = _get_val(a, "details", "")
            prev_h = _get_val(a, "previous_hash") or _get_val(a, "prev_hash") or ""
            entry_h = _get_val(a, "entry_hash") or _get_val(a, "hash") or ""
            hash_info = f"<br/><font size='7' color='#64748b'>Block: {entry_h[:16]}... | Prev: {prev_h[:16]}...</font>" if entry_h else ""

            audit_data.append([
                Paragraph(ts_str, body_style),
                Paragraph(f"<b>{actor}</b>", body_style),
                Paragraph(action, body_style),
                Paragraph(f"{str(details)[:140]}{hash_info}", body_style)
            ])

        audit_table = Table(audit_data, colWidths=[90, 85, 115, 250])
        audit_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_primary),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light_bg]),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(audit_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
