import os
import hashlib
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Check for PIL and imagehash
try:
    from PIL import Image
    import imagehash
    HAVE_IMAGEHASH = True
except ImportError:
    HAVE_IMAGEHASH = False
    logger.warning("imagehash or Pillow is not installed. Perceptual hashing will be unavailable.")


def compute_file_hash(file_path: str) -> str:
    """Compute the SHA-256 hash of a file's binary content."""
    if not os.path.exists(file_path):
        return ""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_bytes_hash(data: bytes) -> str:
    """Compute SHA-256 hash from in-memory bytes."""
    return hashlib.sha256(data).hexdigest()


def check_exact_duplicates(documents: list[dict], application_id: str = "") -> list[dict]:
    """
    Check for exact duplicate files using SHA-256 hash matching.
    documents: list of dicts with keys: id, filename, file_hash, file_path (optional)
    Returns: list of Finding dicts with finding_type="duplicate" and severity="high"
    """
    if not documents or len(documents) < 2:
        return []

    hash_map: dict[str, list[dict]] = {}
    for doc in documents:
        doc_hash = doc.get("file_hash")
        # If file_hash is not precomputed but file_path exists, compute it
        if not doc_hash and doc.get("file_path") and os.path.exists(doc.get("file_path")):
            doc_hash = compute_file_hash(doc.get("file_path"))
            doc["file_hash"] = doc_hash

        if doc_hash:
            hash_map.setdefault(doc_hash, []).append(doc)

    findings: list[dict] = []
    for h, docs in hash_map.items():
        if len(docs) > 1:
            first_doc = docs[0]
            # Flag every subsequent duplicate
            for dup in docs[1:]:
                findings.append({
                    "id": str(uuid.uuid4()),
                    "application_id": application_id,
                    "document_id": dup.get("id"),
                    "finding_type": "duplicate",
                    "severity": "high",
                    "title": f"Exact Duplicate Document: {dup.get('filename')}",
                    "description": (
                        f"Document '{dup.get('filename')}' is an exact byte-for-byte duplicate of "
                        f"'{first_doc.get('filename')}' (SHA-256 match)."
                    ),
                    "evidence": f"Identical SHA-256 hash: {h}",
                    "rule_id": "DUP-EXACT-001",
                    "rule_version": "1.0",
                    "field_name": "file_hash",
                    "page_number": 0,
                    "review_status": "pending",
                    "review_comment": None,
                    "reviewed_by": None,
                    "reviewed_at": None,
                    "created_at": datetime.utcnow()
                })

    return findings


def check_perceptual_duplicates(
    documents: list[dict],
    application_id: str = "",
    threshold: int = 10
) -> list[dict]:
    """
    Detect visually near-duplicate images using perceptual hashing (pHash).
    Only applies to image files (jpg, jpeg, png, bmp, webp).
    Threshold: Hamming distance < 10 signifies high visual similarity.
    """
    if not HAVE_IMAGEHASH:
        logger.info("Perceptual duplicate check skipped: imagehash library not available.")
        return []

    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    image_docs: list[dict] = []

    for doc in documents:
        file_path = doc.get("file_path", "")
        filename = doc.get("filename", "")
        ext = os.path.splitext(filename.lower())[1]
        if ext in image_extensions and file_path and os.path.exists(file_path):
            try:
                with Image.open(file_path) as img:
                    ph = imagehash.phash(img)
                    image_docs.append({
                        "doc": doc,
                        "phash": ph
                    })
            except Exception as e:
                logger.warning(f"Could not compute pHash for {filename}: {e}")

    if len(image_docs) < 2:
        return []

    findings: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()

    for i in range(len(image_docs)):
        item1 = image_docs[i]
        doc1 = item1["doc"]
        h1 = item1["phash"]

        for j in range(i + 1, len(image_docs)):
            item2 = image_docs[j]
            doc2 = item2["doc"]
            h2 = item2["phash"]

            distance = h1 - h2
            if distance < threshold:
                pair_key = tuple(sorted([doc1.get("id", ""), doc2.get("id", "")]))
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    findings.append({
                        "id": str(uuid.uuid4()),
                        "application_id": application_id,
                        "document_id": doc2.get("id"),
                        "finding_type": "duplicate",
                        "severity": "medium",
                        "title": f"Near-Duplicate Image Detected: {doc2.get('filename')}",
                        "description": (
                            f"Image '{doc2.get('filename')}' is visually very similar to "
                            f"'{doc1.get('filename')}' (Hamming distance: {distance})."
                        ),
                        "evidence": f"pHash distance: {distance} (< {threshold} threshold). Hash 1: {h1}, Hash 2: {h2}",
                        "rule_id": "DUP-PHASH-001",
                        "rule_version": "1.0",
                        "field_name": "image_content",
                        "page_number": 0,
                        "review_status": "pending",
                        "review_comment": None,
                        "reviewed_by": None,
                        "reviewed_at": None,
                        "created_at": datetime.utcnow()
                    })

    return findings
