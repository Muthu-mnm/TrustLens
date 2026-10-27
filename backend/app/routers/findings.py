"""Findings router – officer review actions."""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.services import audit_service

logger = logging.getLogger(__name__)
router = APIRouter()

VALID_STATUSES = {"reviewed", "dismissed", "clarification_needed"}


@router.post("/{finding_id}/review", response_model=schemas.FindingResponse)
def review_finding(
    finding_id: str,
    payload: schemas.ReviewActionRequest,
    db: Session = Depends(get_db),
):
    finding = db.query(models.Finding).filter(models.Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found.")

    if payload.review_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid review_status. Must be one of: {', '.join(VALID_STATUSES)}",
        )

    if payload.review_status == "dismissed" and not (payload.comment or "").strip():
        raise HTTPException(
            status_code=400,
            detail="A dismissal reason (comment) is required when dismissing a finding.",
        )

    finding.review_status = payload.review_status
    finding.review_comment = payload.comment or ""
    finding.reviewed_by = payload.reviewed_by or "Officer"
    finding.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(finding)

    audit_service.create_audit_entry(
        db,
        finding.application_id,
        "FINDING_REVIEWED",
        payload.reviewed_by or "Officer",
        (
            f"Finding '{finding.title}' marked as '{payload.review_status}'. "
            f"Comment: {payload.comment or '(none)'}"
        ),
    )

    return schemas.FindingResponse.model_validate(finding)


@router.get("/{finding_id}", response_model=schemas.FindingResponse)
def get_finding(finding_id: str, db: Session = Depends(get_db)):
    finding = db.query(models.Finding).filter(models.Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found.")
    return schemas.FindingResponse.model_validate(finding)
