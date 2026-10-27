"""Documents router â€“ file upload, listing and preview."""
import hashlib
import io
import os
import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.services import ocr_service

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "./uploads")
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "20"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

ALLOWED_MIME = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/tiff": "tiff",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@router.post("/applications/{app_id}/documents", response_model=List[schemas.DocumentResponse])
async def upload_documents(
    app_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    app_obj = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found.")

    save_dir = os.path.join(UPLOAD_DIR, app_id)
    os.makedirs(save_dir, exist_ok=True)

    saved_docs = []
    for upload in files:
        content = await upload.read()

        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File '{upload.filename}' exceeds {MAX_UPLOAD_MB} MB limit.",
            )

        content_type = upload.content_type or ""
        # Try to infer from filename if content_type is generic
        if content_type == "application/octet-stream" and upload.filename:
            ext = upload.filename.rsplit(".", 1)[-1].lower()
            ct_map = {"pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                      "png": "image/png", "tiff": "image/tiff", "tif": "image/tiff"}
            content_type = ct_map.get(ext, content_type)

        if content_type not in ALLOWED_MIME:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{content_type}' not allowed. Accepted: PDF, JPG, PNG, TIFF.",
            )

        file_hash = _sha256(content)
        safe_name = f"{uuid.uuid4().hex}_{upload.filename}"
        file_path = os.path.join(save_dir, safe_name)

        with open(file_path, "wb") as fh:
            fh.write(content)

        # Count pages for PDFs
        page_count = 1
        if content_type == "application/pdf":
            try:
                import pymupdf as fitz  # PyMuPDF (modern import)
                doc = fitz.open(stream=content, filetype="pdf")
                page_count = len(doc)
                doc.close()
            except Exception:
                page_count = 1

        doc_obj = models.Document(
            id=str(uuid.uuid4()),
            application_id=app_id,
            filename=safe_name,
            original_filename=upload.filename,
            doc_type=ALLOWED_MIME[content_type],
            file_hash=file_hash,
            page_count=page_count,
            file_size=len(content),
            mime_type=content_type,
            status="uploaded",
            created_at=datetime.utcnow(),
        )
        db.add(doc_obj)
        db.commit()
        db.refresh(doc_obj)
        saved_docs.append(doc_obj)

    return [schemas.DocumentResponse.model_validate(d) for d in saved_docs]


@router.get("/applications/{app_id}/documents", response_model=List[schemas.DocumentResponse])
def list_documents(app_id: str, db: Session = Depends(get_db)):
    app_obj = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found.")
    docs = db.query(models.Document).filter(models.Document.application_id == app_id).all()
    return [schemas.DocumentResponse.model_validate(d) for d in docs]


@router.get("/documents/{doc_id}/preview")
def preview_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    file_path = os.path.join(UPLOAD_DIR, doc.application_id, doc.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document file not found on disk.")

    try:
        pages = ocr_service.extract_text(file_path, doc.mime_type or "")
        text = "\n\n--- Page Break ---\n\n".join(p.get("text", "") for p in pages)
        return JSONResponse({
            "document_id": doc_id,
            "filename": doc.original_filename,
            "page_count": len(pages),
            "text_preview": text[:5000],
            "truncated": len(text) > 5000,
        })
    except Exception as exc:
        logger.error("Preview error for %s: %s", doc_id, exc)
        return JSONResponse({"document_id": doc_id, "filename": doc.original_filename,
                             "text_preview": f"Preview unavailable: {exc}", "truncated": False})

