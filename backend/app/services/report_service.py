import io
import logging
from datetime import datetime
from typing import Any
from xml.sax.saxutils import escape as xml_escape

logger = logging.getLogger(__name__)

FOOTER_TEXT = "PROTOTYPE - NOT OFFICIAL AICTE SYSTEM. Advisory only. Human review required."

letter = None
colors = None
getSampleStyleSheet = None
ParagraphStyle = None
SimpleDocTemplate = None
Paragraph = None
Spacer = None
Table = None
TableStyle = None
PageBreak = None
HRFlowable = None
canvas = None
HAVE_REPORTLAB = False


def _ensure_reportlab() -> bool:
    """Ensure ReportLab is dynamically loaded into module scope."""
    global HAVE_REPORTLAB, letter, colors, getSampleStyleSheet, ParagraphStyle
    global SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, canvas
    if HAVE_REPORTLAB:
        return True
    try:
        from reportlab.lib.pagesizes import letter as _letter
        from reportlab.lib import colors as _colors
        from reportlab.lib.styles import getSampleStyleSheet as _getSampleStyleSheet, ParagraphStyle as _ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate as _SimpleDocTemplate, Paragraph as _Paragraph, Spacer as _Spacer,
            Table as _Table, TableStyle as _TableStyle, PageBreak as _PageBreak, HRFlowable as _HRFlowable
        )
        from reportlab.pdfgen import canvas as _canvas
        letter = _letter
        colors = _colors
        getSampleStyleSheet = _getSampleStyleSheet
        ParagraphStyle = _ParagraphStyle
        SimpleDocTemplate = _SimpleDocTemplate
        Paragraph = _Paragraph
        Spacer = _Spacer
        Table = _Table
        TableStyle = _TableStyle
        PageBreak = _PageBreak
        HRFlowable = _HRFlowable
        canvas = _canvas
        HAVE_REPORTLAB = True
        return True
    except ImportError:
        HAVE_REPORTLAB = False
        return False


# Try initial import at module load
_ensure_reportlab()


def _get_canvas_maker():
    """Return NumberedCanvas class dynamically subclassing canvas.Canvas."""
    if not _ensure_reportlab() or canvas is None:
        return None

    class NumberedCanvas(canvas.Canvas):
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

    return NumberedCanvas


def _get_val(obj: Any, key: str, default: Any = "") -> Any:
    """Helper to safely extract key from dict or model object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _safe_xml(text: Any) -> str:
    """Safely escape text for ReportLab XML/HTML Paragraph rendering."""
    if text is None:
        return ""
    return xml_escape(str(text))


def _generate_fallback_pdf(
    application_id: str,
    institution_name: str = "AICTE Scrutiny Application",
    risk_band: str = "Under Review"
) -> bytes:
    """Minimal 100% syntactically valid PDF-1.4 fallback with standard fonts and exact xref offsets."""
    safe_app_id = str(application_id).replace("(", "").replace(")", "")
    safe_inst = str(institution_name).replace("(", "").replace(")", "")[:60]
    safe_band = str(risk_band).replace("(", "").replace(")", "")

    lines = [
        "BT",
        "/F2 18 Tf",
        "40 740 Td",
        "(TrustLens - AICTE Scrutiny Dossier) Tj",
        "0 -28 Td",
        "/F1 11 Tf",
        f"(Application ID: {safe_app_id}) Tj",
        "0 -20 Td",
        f"(Institution: {safe_inst}) Tj",
        "0 -20 Td",
        f"(Scrutiny Status: Evaluated - Risk Classification: {safe_band}) Tj",
        "0 -36 Td",
        "/F2 12 Tf",
        "(PROTOTYPE ADVISORY - HUMAN REVIEW REQUIRED) Tj",
        "0 -20 Td",
        "/F1 9 Tf",
        "(This scrutiny evaluation was generated by the TrustLens Decision-Support MVP for SIH26261.) Tj",
        "0 -16 Td",
        "(It does not constitute an official AICTE sanction or rejection. Human officer review is mandatory.) Tj",
        "ET"
    ]
    stream_content = "\n".join(lines)
    stream_bytes = stream_content.encode("latin1", "replace")
    stream_len = len(stream_bytes)

    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>\nendobj\n",
        f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("latin1") + stream_bytes + b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        b"6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n"
    ]

    header = b"%PDF-1.4\n"
    offsets = [0]
    current_offset = len(header)
    parts = [header]

    for obj in objects:
        offsets.append(current_offset)
        parts.append(obj)
        current_offset += len(obj)

    xref_offset = current_offset
    xref_lines = [f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("latin1")]
    for off in offsets[1:]:
        xref_lines.append(f"{off:010d} 00000 n \n".encode("latin1"))

    trailer = (
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("latin1")

    return b"".join(parts) + b"".join(xref_lines) + trailer


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
    inst_name = _get_val(application, "institution_name", "AICTE Scrutiny Application")
    risk_band = _get_val(application, "risk_band", "Low")

    if not _ensure_reportlab():
        return _generate_fallback_pdf(app_id, inst_name, risk_band)

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
    story.append(Paragraph("TrustLens — AICTE Scrutiny Engine", title_style))
    gen_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    story.append(Paragraph(f"Application Scrutiny &amp; Explainable Verification Dossier | Generated: {gen_time}", subtitle_style))

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
    app_type = _get_val(application, "app_type", "Engineering & Technology")
    status = _get_val(application, "status", "analyzed")
    risk_score = _get_val(application, "risk_score", 0.0)
    trust_score = _get_val(application, "trust_score", round(max(0.0, 100.0 - float(risk_score)), 1))
    doc_count = len(documents)

    summary_data = [
        [
            Paragraph("<b>Application ID:</b>", body_style), Paragraph(_safe_xml(app_id), body_style),
            Paragraph("<b>Scrutiny Status:</b>", body_style), Paragraph(_safe_xml(str(status).upper()), body_style)
        ],
        [
            Paragraph("<b>Institution Name:</b>", body_style), Paragraph(_safe_xml(inst_name), body_style),
            Paragraph("<b>Program Type:</b>", body_style), Paragraph(_safe_xml(app_type), body_style)
        ],
        [
            Paragraph("<b>Uploaded Documents:</b>", body_style), Paragraph(f"{doc_count} document(s)", body_style),
            Paragraph("<b>Risk Band / Score:</b>", body_style), Paragraph(f"<b>{_safe_xml(risk_band)}</b> (Risk: {risk_score}/100, Trust: {trust_score}/100)", body_style)
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
                Paragraph(f"<b>{_safe_xml(fname)}</b>", body_style),
                Paragraph(_safe_xml(str(fval)[:100]), body_style),
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
            sev_html = f"<font color='{sev_color}'><b>{_safe_xml(sev.upper())}</b></font>"

            findings_data.append([
                Paragraph(sev_html, body_style),
                Paragraph(f"<b>{_safe_xml(title)}</b>", body_style),
                Paragraph(_safe_xml(ftype), body_style),
                Paragraph(_safe_xml(str(evidence)[:140]), body_style),
                Paragraph(f"<b>{_safe_xml(rstatus)}</b>", body_style)
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
            Paragraph(f"<b>{_safe_xml(risk_band)} Risk</b>", body_style),
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
            hash_info = f"<br/><font size='7' color='#64748b'>Block: {_safe_xml(entry_h[:16])}... | Prev: {_safe_xml(prev_h[:16])}...</font>" if entry_h else ""

            audit_data.append([
                Paragraph(ts_str, body_style),
                Paragraph(f"<b>{_safe_xml(actor)}</b>", body_style),
                Paragraph(_safe_xml(action), body_style),
                Paragraph(f"{_safe_xml(str(details)[:140])}{hash_info}", body_style)
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

    try:
        canvas_maker = _get_canvas_maker()
        if canvas_maker:
            doc.build(story, canvasmaker=canvas_maker)
        else:
            doc.build(story)
        return buffer.getvalue()
    except Exception as exc:
        logger.error("ReportLab document build failed: %s, falling back to basic valid PDF", exc, exc_info=True)
        return _generate_fallback_pdf(app_id, inst_name, risk_band)
