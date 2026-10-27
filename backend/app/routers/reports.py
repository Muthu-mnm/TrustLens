"""Reports router – generate and stream PDF report."""
import io
import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.services import report_service, scoring_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{app_id}/report")
def get_report(app_id: str, db: Session = Depends(get_db)):
    app_obj = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found.")

    docs = db.query(models.Document).filter(models.Document.application_id == app_id).all()
    doc_ids = [d.id for d in docs]

    findings = db.query(models.Finding).filter(models.Finding.application_id == app_id).all()

    extracted = []
    if doc_ids:
        extracted = db.query(models.ExtractedField).filter(
            models.ExtractedField.document_id.in_(doc_ids)
        ).all()

    audit_entries = (
        db.query(models.AuditEntry)
        .filter(models.AuditEntry.application_id == app_id)
        .order_by(models.AuditEntry.created_at.asc())
        .all()
    )

    app_dict = {
        "id": app_obj.id,
        "app_id": app_obj.app_id,
        "app_type": app_obj.app_type,
        "institution_name": app_obj.institution_name,
        "status": app_obj.status,
        "risk_score": app_obj.risk_score,
        "risk_band": app_obj.risk_band,
        "created_at": app_obj.created_at,
        "updated_at": app_obj.updated_at,
    }
    docs_list = [
        {"id": d.id, "original_filename": d.original_filename, "doc_type": d.doc_type,
         "page_count": d.page_count, "status": d.status, "file_hash": d.file_hash}
        for d in docs
    ]
    findings_list = [
        {"id": f.id, "severity": f.severity, "title": f.title, "description": f.description,
         "evidence": f.evidence, "finding_type": f.finding_type, "rule_id": f.rule_id,
         "review_status": f.review_status, "review_comment": f.review_comment,
         "reviewed_by": f.reviewed_by, "document_id": f.document_id}
        for f in findings
    ]
    ef_list = [
        {"field_name": e.field_name, "field_value": e.field_value, "confidence": e.confidence,
         "page_number": e.page_number, "document_id": e.document_id}
        for e in extracted
    ]
    audit_list = [
        {"action": a.action, "actor": a.actor, "details": a.details, "created_at": a.created_at}
        for a in audit_entries
    ]

    try:
        pdf_bytes = report_service.generate_report(
            application=app_dict,
            documents=docs_list,
            findings=findings_list,
            extracted_fields=ef_list,
            audit_entries=audit_list,
        )
    except Exception as exc:
        logger.error("Report generation failed for %s: %s", app_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    filename = f"TrustLens_Report_{app_obj.app_id}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
