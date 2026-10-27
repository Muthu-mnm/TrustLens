"""
Applications router – handles application CRUD and full analysis pipeline.
"""
import os
import uuid
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.services import (
    ocr_service,
    extraction_service,
    validation_service,
    comparison_service,
    duplicate_service,
    ela_service,
    rule_engine,
    scoring_service,
    audit_service,
)

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "./uploads")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _app_response(app: models.Application, db: Session) -> schemas.ApplicationResponse:
    doc_count = db.query(models.Document).filter(models.Document.application_id == app.id).count()
    finding_count = db.query(models.Finding).filter(models.Finding.application_id == app.id).count()
    risk_val = app.risk_score if app.risk_score is not None else 0.0
    trust_val = round(max(0.0, 100.0 - risk_val), 1)
    return schemas.ApplicationResponse(
        id=app.id,
        app_id=app.app_id,
        app_type=app.app_type,
        institution_name=app.institution_name,
        status=app.status,
        created_at=app.created_at,
        updated_at=app.updated_at,
        risk_score=risk_val,
        trust_score=trust_val,
        risk_band=app.risk_band or "Low",
        document_count=doc_count,
        finding_count=finding_count,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", response_model=schemas.ApplicationResponse)
def create_application(payload: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Application).filter(models.Application.app_id == payload.app_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Application with app_id '{payload.app_id}' already exists.")
    app_obj = models.Application(
        id=str(uuid.uuid4()),
        app_id=payload.app_id,
        app_type=payload.app_type,
        institution_name=payload.institution_name,
        status="uploaded",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(app_obj)
    db.commit()
    db.refresh(app_obj)
    audit_service.create_audit_entry(db, app_obj.id, "APPLICATION_CREATED", "system",
                                     f"Application '{payload.app_id}' created for '{payload.institution_name}'.")
    return _app_response(app_obj, db)


@router.get("", response_model=List[schemas.ApplicationResponse])
def list_applications(db: Session = Depends(get_db)):
    apps = db.query(models.Application).order_by(models.Application.created_at.desc()).all()
    return [_app_response(a, db) for a in apps]


@router.get("/{app_id}", response_model=schemas.ApplicationResponse)
def get_application(app_id: str, db: Session = Depends(get_db)):
    app_obj = db.query(models.Application).filter(
        (models.Application.id == app_id) | (models.Application.app_id == app_id)
    ).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found.")
    return _app_response(app_obj, db)


@router.post("/{app_id}/analyze", response_model=schemas.AnalysisResultResponse)
def analyze_application(app_id: str, db: Session = Depends(get_db)):
    app_obj = db.query(models.Application).filter(
        (models.Application.id == app_id) | (models.Application.app_id == app_id)
    ).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found.")

    target_app_id = app_obj.id
    docs = db.query(models.Document).filter(models.Document.application_id == target_app_id).all()
    if not docs:
        raise HTTPException(status_code=400, detail="No documents uploaded for this application.")

    # Update status
    app_obj.status = "analyzing"
    app_obj.updated_at = datetime.utcnow()
    db.commit()

    # Clear previous results
    db.query(models.ExtractedField).filter(
        models.ExtractedField.document_id.in_([d.id for d in docs])
    ).delete(synchronize_session=False)
    db.query(models.Finding).filter(models.Finding.application_id == target_app_id).delete(synchronize_session=False)
    db.commit()

    all_findings: list[dict] = []
    all_extracted: list[dict] = []
    doc_field_sets: list[dict] = []
    doc_info_for_dup: list[dict] = []

    # ── Step 1-4: OCR + Field Extraction per document ────────────────────────
    for doc in docs:
        file_path = os.path.join(UPLOAD_DIR, target_app_id, doc.filename)
        if not os.path.exists(file_path):
            logger.warning("File not found: %s", file_path)
            doc.status = "error"
            doc.error_message = "File not found on disk."
            db.commit()
            all_findings.append({
                "application_id": target_app_id,
                "document_id": doc.id,
                "finding_type": "compliance",
                "severity": "medium",
                "title": f"Document Not Found: {doc.original_filename}",
                "description": f"File '{doc.original_filename}' missing from upload storage.",
                "evidence": f"File path {file_path} not found.",
                "rule_id": "SYS-001",
                "rule_version": "1.0",
                "field_name": "",
                "page_number": 0,
            })
            continue

        doc.status = "processing"
        db.commit()

        try:
            pages = ocr_service.extract_text(file_path, doc.mime_type or "")
            fields = extraction_service.extract_fields(pages)

            # Persist extracted fields
            for f in fields:
                ef = models.ExtractedField(
                    id=str(uuid.uuid4()),
                    document_id=doc.id,
                    field_name=f["field_name"],
                    field_value=f["field_value"],
                    confidence=f.get("confidence", 0.5),
                    page_number=f.get("page_number", 1),
                    created_at=datetime.utcnow(),
                )
                db.add(ef)
                all_extracted.append({
                    **f,
                    "id": ef.id,
                    "document_id": doc.id,
                    "document_filename": doc.original_filename
                })

            doc_field_sets.append({
                "document_id": doc.id,
                "filename": doc.original_filename,
                "fields": [{"field_name": f["field_name"], "field_value": f["field_value"]} for f in fields],
            })
            doc_info_for_dup.append({
                "id": doc.id,
                "filename": doc.original_filename,
                "file_hash": doc.file_hash or "",
                "file_path": file_path,
                "mime_type": doc.mime_type or "",
            })

            # ── Step 8b: ELA for images ──────────────────────────────────────
            if doc.mime_type and doc.mime_type.startswith("image/"):
                ela_dir = os.path.join(UPLOAD_DIR, target_app_id, "ela")
                os.makedirs(ela_dir, exist_ok=True)
                ela_result = ela_service.run_ela(file_path, ela_dir)
                if ela_result.get("anomaly_detected"):
                    all_findings.append({
                        "application_id": target_app_id,
                        "document_id": doc.id,
                        "finding_type": "ela_anomaly",
                        "severity": "medium",
                        "title": f"ELA Anomaly Detected in {doc.original_filename}",
                        "description": (
                            "Error-Level Analysis detected unusual pixel-level patterns. "
                            "This is a heuristic indicator only — it does NOT confirm tampering. "
                            "A qualified officer should inspect the original document."
                        ),
                        "evidence": (
                            f"Mean ELA error: {ela_result.get('mean_error', 0):.2f} "
                            f"(threshold: 15.0). {ela_result.get('warning', '')}"
                        ),
                        "rule_id": "ELA-001",
                        "rule_version": "1.0",
                        "field_name": "",
                        "page_number": 1,
                    })

            doc.status = "processed"
            db.commit()

        except Exception as exc:
            logger.error("Error processing document %s: %s", doc.id, exc, exc_info=True)
            doc.status = "error"
            doc.error_message = str(exc)[:500]
            db.commit()
            all_findings.append({
                "application_id": target_app_id,
                "document_id": doc.id,
                "finding_type": "compliance",
                "severity": "medium",
                "title": f"Document Processing Warning: {doc.original_filename}",
                "description": f"Automated text extraction encountered an error: {str(exc)[:200]}. Manual officer inspection recommended.",
                "evidence": f"File '{doc.original_filename}' processing status set to error.",
                "rule_id": "DOC-ERR-001",
                "rule_version": "1.0",
                "field_name": "",
                "page_number": 0,
            })

    db.commit()

    # ── Step 5: Mandatory field validation across application dossier ────────
    val_findings = validation_service.validate_mandatory_fields(
        all_extracted,
        application_id=target_app_id,
        filename=docs[0].original_filename if len(docs) == 1 else "Application Dossier"
    )
    for vf in val_findings:
        vf["application_id"] = target_app_id
    all_findings.extend(val_findings)

    # ── Step 6: Cross-document comparison ────────────────────────────────────
    if len(doc_field_sets) > 1:
        mismatch_findings = comparison_service.compare_documents(doc_field_sets, application_id=target_app_id)
        for mf in mismatch_findings:
            mf["application_id"] = target_app_id
        all_findings.extend(mismatch_findings)

    # ── Step 7: Duplicate detection ──────────────────────────────────────────
    dup_findings = duplicate_service.check_exact_duplicates(doc_info_for_dup, application_id=target_app_id)
    for df in dup_findings:
        df["application_id"] = target_app_id
    all_findings.extend(dup_findings)

    perc_findings = duplicate_service.check_perceptual_duplicates(doc_info_for_dup, application_id=target_app_id)
    for pf in perc_findings:
        pf["application_id"] = target_app_id
    all_findings.extend(perc_findings)

    # ── Step 9: Compliance rules ──────────────────────────────────────────────
    rule_findings = rule_engine.evaluate_rules(all_extracted, {"id": target_app_id, "app_type": app_obj.app_type})
    for rf in rule_findings:
        rf["application_id"] = target_app_id
    all_findings.extend(rule_findings)

    # ── Step 10-11: Save findings + score ────────────────────────────────────
    saved_findings = []
    for fd in all_findings:
        finding = models.Finding(
            id=str(uuid.uuid4()),
            application_id=fd.get("application_id", target_app_id),
            document_id=fd.get("document_id"),
            finding_type=fd.get("finding_type", "compliance"),
            severity=fd.get("severity", "info"),
            title=fd.get("title", "Finding"),
            description=fd.get("description", ""),
            evidence=fd.get("evidence", ""),
            rule_id=fd.get("rule_id", ""),
            rule_version=fd.get("rule_version", ""),
            field_name=fd.get("field_name", ""),
            page_number=fd.get("page_number", 0),
            review_status="pending",
            created_at=datetime.utcnow(),
        )
        db.add(finding)
        saved_findings.append(finding)
    db.commit()

    score_result = scoring_service.calculate_risk_score(all_findings)
    app_obj.risk_score = score_result["risk_score"]
    app_obj.risk_band = score_result["band"]
    app_obj.status = "analyzed"
    app_obj.updated_at = datetime.utcnow()
    db.commit()

    audit_service.create_audit_entry(
        db, target_app_id, "ANALYSIS_COMPLETED", "system",
        f"Analysis complete. Findings: {len(saved_findings)}. "
        f"Risk score: {score_result['risk_score']:.1f} ({score_result['band']}). "
        f"Trust score: {score_result['trust_score']:.1f}."
    )

    # Build response
    ef_responses = [
        schemas.ExtractedFieldResponse(
            id=e.get("id") or str(uuid.uuid4()),
            document_id=e["document_id"],
            field_name=e["field_name"],
            field_value=e["field_value"],
            confidence=e.get("confidence", 0.5),
            page_number=e.get("page_number", 1),
        )
        for e in all_extracted
    ]
    finding_responses = [schemas.FindingResponse.model_validate(f) for f in saved_findings]

    return schemas.AnalysisResultResponse(
        application_id=target_app_id,
        status="analyzed",
        extracted_fields=ef_responses,
        findings=finding_responses,
        risk_score=score_result["risk_score"],
        trust_score=score_result["trust_score"],
        risk_band=score_result["band"],
        score_breakdown=score_result["breakdown"],
        score_explanation=score_result["explanation"],
        analyzed_at=datetime.utcnow(),
    )


@router.get("/{app_id}/results", response_model=schemas.AnalysisResultResponse)
@router.get("/{app_id}/findings", response_model=schemas.AnalysisResultResponse, include_in_schema=False)
def get_results(app_id: str, db: Session = Depends(get_db)):
    app_obj = db.query(models.Application).filter(
        (models.Application.id == app_id) | (models.Application.app_id == app_id)
    ).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found.")

    target_app_id = app_obj.id
    docs = db.query(models.Document).filter(models.Document.application_id == target_app_id).all()
    doc_ids = [d.id for d in docs]

    extracted = db.query(models.ExtractedField).filter(
        models.ExtractedField.document_id.in_(doc_ids)
    ).all() if doc_ids else []

    findings = db.query(models.Finding).filter(
        models.Finding.application_id == target_app_id
    ).all()

    all_findings_dicts = [{"severity": f.severity} for f in findings]
    score_result = scoring_service.calculate_risk_score(all_findings_dicts)
    resolved_risk_score = app_obj.risk_score if app_obj.risk_score is not None else score_result["risk_score"]
    resolved_trust_score = round(max(0.0, 100.0 - resolved_risk_score), 1)

    return schemas.AnalysisResultResponse(
        application_id=target_app_id,
        status=app_obj.status,
        extracted_fields=[schemas.ExtractedFieldResponse.model_validate(e) for e in extracted],
        findings=[schemas.FindingResponse.model_validate(f) for f in findings],
        risk_score=resolved_risk_score,
        trust_score=resolved_trust_score,
        risk_band=app_obj.risk_band or score_result["band"],
        score_breakdown=score_result["breakdown"],
        score_explanation=score_result["explanation"],
        analyzed_at=app_obj.updated_at,
    )


@router.get("/{app_id}/audit", response_model=List[schemas.AuditEntryResponse])
@router.get("/{app_id}/audit-trail", response_model=List[schemas.AuditEntryResponse], include_in_schema=False)
def get_audit(app_id: str, db: Session = Depends(get_db)):
    app_obj = db.query(models.Application).filter(
        (models.Application.id == app_id) | (models.Application.app_id == app_id)
    ).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found.")
    entries = (
        db.query(models.AuditEntry)
        .filter(models.AuditEntry.application_id == app_obj.id)
        .order_by(models.AuditEntry.created_at.desc(), models.AuditEntry.id.desc())
        .all()
    )
    return [schemas.AuditEntryResponse.model_validate(e) for e in entries]


@router.get("/{app_id}/audit/verify", response_model=schemas.AuditVerificationResponse)
def verify_audit(app_id: str, db: Session = Depends(get_db)):
    app_obj = db.query(models.Application).filter(
        (models.Application.id == app_id) | (models.Application.app_id == app_id)
    ).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found.")
    return audit_service.verify_audit_chain(db, app_obj.id)
