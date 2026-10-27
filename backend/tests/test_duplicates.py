import pytest
from app.services.duplicate_service import (
    check_exact_duplicates,
    check_perceptual_duplicates,
    HAVE_IMAGEHASH
)


def test_exact_duplicate_detection():
    """Verify that identical SHA-256 hashes across documents generate duplicate findings."""
    identical_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    documents = [
        {
            "id": "doc-uuid-1",
            "filename": "original_affidavit.pdf",
            "file_hash": identical_hash
        },
        {
            "id": "doc-uuid-2",
            "filename": "duplicate_affidavit_copy.pdf",
            "file_hash": identical_hash
        }
    ]

    findings = check_exact_duplicates(documents, application_id="app-1")

    assert len(findings) == 1
    dup_finding = findings[0]
    assert dup_finding["finding_type"] == "duplicate"
    assert dup_finding["severity"] == "high"
    assert dup_finding["document_id"] == "doc-uuid-2"
    assert "Exact Duplicate Document" in dup_finding["title"]


def test_no_duplicate():
    """Verify that distinct document hashes do not trigger duplicate findings."""
    documents = [
        {
            "id": "doc-uuid-1",
            "filename": "document_a.pdf",
            "file_hash": "aaaa1111222233334444555566667777888899990000aaaabbbbccccddddeeee"
        },
        {
            "id": "doc-uuid-2",
            "filename": "document_b.pdf",
            "file_hash": "bbbb1111222233334444555566667777888899990000aaaabbbbccccddddeeee"
        }
    ]

    findings = check_exact_duplicates(documents, application_id="app-1")
    assert len(findings) == 0


def test_perceptual_hash(sample_image_path):
    """Verify perceptual duplicate detection on images (or skip if imagehash not installed)."""
    if not HAVE_IMAGEHASH:
        pytest.skip("imagehash is not installed in the environment.")

    documents = [
        {
            "id": "img-1",
            "filename": "stamp1.jpg",
            "file_path": sample_image_path
        },
        {
            "id": "img-2",
            "filename": "stamp2.jpg",
            "file_path": sample_image_path
        }
    ]

    findings = check_perceptual_duplicates(documents, application_id="app-1", threshold=10)
    assert len(findings) == 1
    assert findings[0]["finding_type"] == "duplicate"
    assert findings[0]["severity"] == "medium"
