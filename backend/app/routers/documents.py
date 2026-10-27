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
import re
from app.services import ocr_service, audit_service

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


@router.post("/applications/{app_id}/documents", response_model=List[schemas.DocumentResponse])
async def upload_documents(
    app_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    app_obj = db.query(models.Application).filter(
        (models.Application.id == app_id) | (models.Application.app_id == app_id)
    ).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found.")

    target_app_id = app_obj.id
    save_dir = os.path.join(UPLOAD_DIR, target_app_id)
    os.makedirs(save_dir, exist_ok=True)

    saved_docs = []
    for upload in files:
        raw_basename = os.path.basename(upload.filename or "uploaded_file")
        clean_name = re.sub(r"[^\w\.\-]", "_", raw_basename)
        safe_name = f"{uuid.uuid4().hex}_{clean_name}"
        file_path = os.path.join(save_dir, safe_name)

        content_type = upload.content_type or ""
        if (not content_type or content_type == "application/octet-stream") and upload.filename:
            ext = upload.filename.rsplit(".", 1)[-1].lower()
            ct_map = {
                "pdf": "application/pdf",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "tiff": "image/tiff",
                "tif": "image/tiff",
            }
            content_type = ct_map.get(ext, content_type)

        if content_type not in ALLOWED_MIME:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{content_type}' not allowed. Accepted: PDF, JPG, PNG, TIFF.",
            )

        # Chunked streaming write to enforce upload limit without unbounded memory consumption
        hasher = hashlib.sha256()
        file_size = 0
        header_chunk = b""

        try:
            with open(file_path, "wb") as fh:
                while True:
                    chunk = await upload.read(65536)
                    if not chunk:
                        break
                    file_size += len(chunk)
                    if file_size > MAX_UPLOAD_BYTES:
                        fh.close()
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        raise HTTPException(
                            status_code=400,
                            detail=f"File '{raw_basename}' exceeds {MAX_UPLOAD_MB} MB limit.",
                        )
                    if len(header_chunk) < 16:
                        header_chunk += chunk[:16 - len(header_chunk)]
                    hasher.update(chunk)
                    fh.write(chunk)
        except HTTPException:
            raise
        except Exception as exc:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Storage error saving '{raw_basename}': {exc}")

        if file_size == 0:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"File '{raw_basename}' is empty (0 bytes).")

        # Validate file header / magic bytes
        is_valid_header = True
        if content_type == "application/pdf":
            is_valid_header = header_chunk.startswith(b"%PDF")
        elif content_type in ("image/jpeg", "image/jpg"):
            is_valid_header = header_chunk.startswith(b"\xff\xd8\xff")
        elif content_type == "image/png":
            is_valid_header = header_chunk.startswith(b"\x89PNG\r\n\x1a\n")
        elif content_type == "image/tiff":
            is_valid_header = header_chunk.startswith(b"II*\x00") or header_chunk.startswith(b"MM\x00*")

        if not is_valid_header:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail=f"File signature mismatch for '{raw_basename}'. Declared {content_type} but signature is invalid.",
            )

        file_hash = hasher.hexdigest()

        # Count pages for PDFs
        page_count = 1
        if content_type == "application/pdf":
            try:
                try:
                    import pymupdf as fitz
                except ImportError:
                    import fitz
                doc = fitz.open(file_path)
                page_count = len(doc)
                doc.close()
            except Exception:
                page_count = 1

        doc_obj = models.Document(
            id=str(uuid.uuid4()),
            application_id=target_app_id,
            filename=safe_name,
            original_filename=raw_basename,
            doc_type=ALLOWED_MIME[content_type],
            file_hash=file_hash,
            page_count=page_count,
            file_size=file_size,
            mime_type=content_type,
            status="uploaded",
            created_at=datetime.utcnow(),
        )
        db.add(doc_obj)
        db.commit()
        db.refresh(doc_obj)
        saved_docs.append(doc_obj)

    if saved_docs:
        audit_service.create_audit_entry(
            db,
            target_app_id,
            "DOCUMENTS_UPLOADED",
            "system",
            f"Uploaded {len(saved_docs)} document(s): {', '.join(d.original_filename for d in saved_docs)}."
        )

    return [schemas.DocumentResponse.model_validate(d) for d in saved_docs]


@router.get("/applications/{app_id}/documents", response_model=List[schemas.DocumentResponse])
def list_documents(app_id: str, db: Session = Depends(get_db)):
    app_obj = db.query(models.Application).filter(
        (models.Application.id == app_id) | (models.Application.app_id == app_id)
    ).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found.")
    docs = db.query(models.Document).filter(models.Document.application_id == app_obj.id).all()
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
        preview_text = text[:5000] if text else "No text extracted from this document."
        return JSONResponse({
            "document_id": doc_id,
            "filename": doc.original_filename,
            "page_count": len(pages),
            "text": preview_text,
            "text_preview": preview_text,
            "preview": preview_text,
            "truncated": len(text) > 5000,
        })
    except Exception as exc:
        logger.error("Preview error for %s: %s", doc_id, exc)
        err_msg = f"Preview unavailable: {exc}"
        return JSONResponse({
            "document_id": doc_id,
            "filename": doc.original_filename,
            "text": err_msg,
            "text_preview": err_msg,
            "preview": err_msg,
            "truncated": False,
        })

