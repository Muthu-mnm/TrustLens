"""
API integration tests for TrustLens backend.
Tests all major endpoints end-to-end using FastAPI TestClient.
"""
import io
import uuid
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_app(client, name="Test Engineering College", app_id=None):
    """Create an application and return the response JSON."""
    payload = {
        "institution_name": name,
        "app_type": "New Technical Institution",
        "app_id": app_id or f"TEST-{uuid.uuid4().hex[:8].upper()}",
    }
    return client.post("/api/applications", json=payload)


# ── Health ────────────────────────────────────────────────────────────────────

def test_health(client):
    """Verify API health status endpoint returns 200 and valid JSON."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "TrustLens" in data["service"]


# ── Application CRUD ──────────────────────────────────────────────────────────

def test_create_application(client):
    """Verify application creation returns 200 and a generated ID."""
    res = _make_app(client, "Test Engineering College of Technology")
    assert res.status_code in (200, 201), f"Got {res.status_code}: {res.text}"
    data = res.json()
    assert "id" in data
    assert data["institution_name"] == "Test Engineering College of Technology"
    assert data["status"] == "uploaded"


def test_create_duplicate_app_id(client):
    """Creating two applications with the same app_id should return 400."""
    fixed_id = f"DUP-{uuid.uuid4().hex[:6].upper()}"
    res1 = _make_app(client, "First College", app_id=fixed_id)
    assert res1.status_code == 200
    res2 = _make_app(client, "Second College", app_id=fixed_id)
    assert res2.status_code == 400


def test_list_applications(client):
    """Verify listing applications returns 200 and a list."""
    _make_app(client, "List Test College")
    response = client.get("/api/applications")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_application(client):
    """Verify fetching a single application by ID."""
    res = _make_app(client, "Get Test College")
    app_id = res.json()["id"]
    response = client.get(f"/api/applications/{app_id}")
    assert response.status_code == 200
    assert response.json()["id"] == app_id


def test_get_application_not_found(client):
    """Fetching a non-existent application should return 404."""
    response = client.get("/api/applications/non-existent-uuid-9999")
    assert response.status_code == 404


# ── Document Upload ────────────────────────────────────────────────────────────

def test_upload_document(client, sample_pdf_path):
    """Verify document upload succeeds and returns DocumentResponse."""
    app_id = _make_app(client, "Upload Target Institute").json()["id"]

    with open(sample_pdf_path, "rb") as f:
        response = client.post(
            f"/api/applications/{app_id}/documents",
            files=[("files", ("sample.pdf", f, "application/pdf"))],
        )

    assert response.status_code in (200, 201), f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["application_id"] == app_id
    assert "file_hash" in data[0]
    assert data[0]["status"] == "uploaded"


def test_upload_multiple_documents(client, sample_pdf_path, sample_image_path):
    """Verify uploading multiple files at once."""
    app_id = _make_app(client, "Multi-Upload Institute").json()["id"]

    with open(sample_pdf_path, "rb") as f1, open(sample_image_path, "rb") as f2:
        response = client.post(
            f"/api/applications/{app_id}/documents",
            files=[
                ("files", ("doc1.pdf", f1, "application/pdf")),
                ("files", ("doc2.jpg", f2, "image/jpeg")),
            ],
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_upload_invalid_type(client, sample_pdf_path):
    """Verify uploading an unpermitted file format returns 400 Bad Request."""
    app_id = _make_app(client, "Invalid File Test Institute").json()["id"]

    fake_file = io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00")
    response = client.post(
        f"/api/applications/{app_id}/documents",
        files=[("files", ("malicious.exe", fake_file, "application/x-msdownload"))],
    )
    assert response.status_code == 400


def test_upload_missing_app(client, sample_pdf_path):
    """Verify uploading to a non-existent application returns 404."""
    with open(sample_pdf_path, "rb") as f:
        response = client.post(
            "/api/applications/non-existent-app-uuid-9999/documents",
            files=[("files", ("sample.pdf", f, "application/pdf"))],
        )
    assert response.status_code == 404


def test_list_documents(client, sample_pdf_path):
    """Verify listing documents for an application."""
    app_id = _make_app(client, "List Docs College").json()["id"]
    with open(sample_pdf_path, "rb") as f:
        client.post(
            f"/api/applications/{app_id}/documents",
            files=[("files", ("doc.pdf", f, "application/pdf"))],
        )
    response = client.get(f"/api/applications/{app_id}/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


# ── Analysis Pipeline ─────────────────────────────────────────────────────────

def test_analyze_application(client, sample_pdf_path):
    """Verify analysis pipeline executes and returns findings and scores."""
    app_id = _make_app(client, "Analysis Pipeline Test Institute").json()["id"]

    with open(sample_pdf_path, "rb") as f:
        client.post(
            f"/api/applications/{app_id}/documents",
            files=[("files", ("scrutiny_doc.pdf", f, "application/pdf"))],
        )

    response = client.post(f"/api/applications/{app_id}/analyze")
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["application_id"] == app_id
    assert data["status"] == "analyzed"
    assert "risk_score" in data
    assert "risk_band" in data
    assert "findings" in data
    assert "score_breakdown" in data
    assert isinstance(data["findings"], list)
    assert isinstance(data["extracted_fields"], list)


def test_analyze_no_documents(client):
    """Verifying analysis fails gracefully when no documents uploaded."""
    app_id = _make_app(client, "Empty Doc College").json()["id"]
    response = client.post(f"/api/applications/{app_id}/analyze")
    assert response.status_code == 400


def test_get_results(client, sample_pdf_path):
    """Verify retrieving cached analysis results after analysis."""
    app_id = _make_app(client, "Results Test College").json()["id"]
    with open(sample_pdf_path, "rb") as f:
        client.post(
            f"/api/applications/{app_id}/documents",
            files=[("files", ("doc.pdf", f, "application/pdf"))],
        )
    client.post(f"/api/applications/{app_id}/analyze")
    response = client.get(f"/api/applications/{app_id}/results")
    assert response.status_code == 200
    data = response.json()
    assert data["application_id"] == app_id
    assert "findings" in data


# ── Finding Review ─────────────────────────────────────────────────────────────

# ── Finding Review ─────────────────────────────────────────────────────────────

def test_review_finding(client, sample_incomplete_pdf_path):
    """Verify officer can review a finding and it persists."""
    app_id = _make_app(client, "Review Action College").json()["id"]
    with open(sample_incomplete_pdf_path, "rb") as f:
        client.post(
            f"/api/applications/{app_id}/documents",
            files=[("files", ("incomplete.pdf", f, "application/pdf"))],
        )
    analysis = client.post(f"/api/applications/{app_id}/analyze").json()
    findings = analysis.get("findings", [])
    assert len(findings) > 0, "Expected findings from incomplete application document"

    finding_id = findings[0]["id"]
    review_res = client.post(
        f"/api/findings/{finding_id}/review",
        json={
            "review_status": "reviewed",
            "comment": "Verified by officer during test run.",
            "reviewed_by": "Test Officer",
        },
    )
    assert review_res.status_code == 200
    data = review_res.json()
    assert data["review_status"] == "reviewed"
    assert data["reviewed_by"] == "Test Officer"


def test_review_dismissal_requires_comment(client, sample_incomplete_pdf_path):
    """Verify dismissing a finding requires a non-empty officer reason/comment."""
    app_id = _make_app(client, "Dismissal Reason Test College").json()["id"]
    with open(sample_incomplete_pdf_path, "rb") as f:
        client.post(
            f"/api/applications/{app_id}/documents",
            files=[("files", ("incomplete.pdf", f, "application/pdf"))],
        )
    analysis = client.post(f"/api/applications/{app_id}/analyze").json()
    findings = analysis.get("findings", [])
    assert len(findings) > 0
    finding_id = findings[0]["id"]

    # Attempt to dismiss without a comment -> should fail with 400
    bad_res = client.post(
        f"/api/findings/{finding_id}/review",
        json={"review_status": "dismissed", "comment": "", "reviewed_by": "Officer Rao"},
    )
    assert bad_res.status_code == 400
    assert "dismissal reason" in bad_res.json()["detail"].lower()

    # Dismiss with a valid reason -> should succeed
    good_res = client.post(
        f"/api/findings/{finding_id}/review",
        json={
            "review_status": "dismissed",
            "comment": "Exempted as per AICTE Special Category Circular 2024.",
            "reviewed_by": "Officer Rao",
        },
    )
    assert good_res.status_code == 200
    assert good_res.json()["review_status"] == "dismissed"


def test_review_invalid_status(client, sample_incomplete_pdf_path):
    """Verify invalid review status returns 400."""
    app_id = _make_app(client, "Invalid Review College").json()["id"]
    with open(sample_incomplete_pdf_path, "rb") as f:
        client.post(
            f"/api/applications/{app_id}/documents",
            files=[("files", ("incomplete.pdf", f, "application/pdf"))],
        )
    analysis = client.post(f"/api/applications/{app_id}/analyze").json()
    findings = analysis.get("findings", [])
    assert len(findings) > 0

    finding_id = findings[0]["id"]
    res = client.post(
        f"/api/findings/{finding_id}/review",
        json={"review_status": "approved_by_ai", "reviewed_by": "Bot"},
    )
    assert res.status_code == 400


# ── Audit Trail & Cryptographic Chain ─────────────────────────────────────────

def test_get_audit(client):
    """Verify audit trail is populated after application creation."""
    app_id = _make_app(client, "Audit Trail Test College").json()["id"]
    response = client.get(f"/api/applications/{app_id}/audit")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At minimum APPLICATION_CREATED entry
    assert data[0]["action"] == "APPLICATION_CREATED"
    assert "entry_hash" in data[0]
    assert "previous_hash" in data[0]


def test_audit_chain_verification_and_tamper_detection(client, db):
    """Verify audit chain verification succeeds for intact chain and detects tampered entries."""
    from app.models import AuditEntry
    app_res = _make_app(client, "Audit Chain Verification College").json()
    app_id = app_res["id"]

    # Verify intact chain
    verify_res = client.get(f"/api/applications/{app_id}/audit/verify")
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["chain_valid"] is True
    assert v_data["total_entries"] >= 1
    assert v_data["tampered_at_index"] is None

    # Simulate database tampering by modifying details of the entry directly
    entry = db.query(AuditEntry).filter(AuditEntry.application_id == app_id).first()
    assert entry is not None
    entry.details = "Tampered details directly injected into database"
    db.commit()

    # Re-verify -> tampering must be detected
    tamper_check = client.get(f"/api/applications/{app_id}/audit/verify")
    assert tamper_check.status_code == 200
    t_data = tamper_check.json()
    assert t_data["chain_valid"] is False
    assert t_data["tampered_at_index"] is not None


# ── Document Preview & Safe Storage ───────────────────────────────────────────

def test_document_preview(client, sample_pdf_path):
    """Verify document preview endpoint returns text preview."""
    app_id = _make_app(client, "Preview Document College").json()["id"]
    with open(sample_pdf_path, "rb") as f:
        up_res = client.post(
            f"/api/applications/{app_id}/documents",
            files=[("files", ("preview_test.pdf", f, "application/pdf"))],
        )
    assert up_res.status_code == 200
    docs = up_res.json()
    assert len(docs) == 1
    doc_id = docs[0]["id"]

    preview_res = client.get(f"/api/documents/{doc_id}/preview")
    assert preview_res.status_code == 200
    prev_data = preview_res.json()
    assert prev_data["document_id"] == doc_id
    assert "text_preview" in prev_data
    assert "ABC College of Engineering" in prev_data["text_preview"]


def test_upload_empty_file_rejected(client):
    """Verify empty 0-byte file is rejected with 400 Bad Request."""
    app_id = _make_app(client, "Empty File College").json()["id"]
    empty_stream = io.BytesIO(b"")
    response = client.post(
        f"/api/applications/{app_id}/documents",
        files=[("files", ("empty.pdf", empty_stream, "application/pdf"))],
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_magic_mismatch_rejected(client):
    """Verify file claiming to be PDF but having text/executable bytes is rejected."""
    app_id = _make_app(client, "Magic Mismatch College").json()["id"]
    fake_pdf = io.BytesIO(b"This is not a real PDF file header.")
    response = client.post(
        f"/api/applications/{app_id}/documents",
        files=[("files", ("fake.pdf", fake_pdf, "application/pdf"))],
    )
    assert response.status_code == 400
    assert "signature" in response.json()["detail"].lower()


# ── Dual-ID Lookup & Idempotency ──────────────────────────────────────────────

def test_dual_id_lookup(client):
    """Verify endpoints resolve applications by both database UUID and human-readable app_id."""
    app_res = _make_app(client, "Dual ID College").json()
    db_uuid = app_res["id"]
    human_app_id = app_res["app_id"]

    # Lookup by UUID
    res1 = client.get(f"/api/applications/{db_uuid}")
    assert res1.status_code == 200
    assert res1.json()["id"] == db_uuid

    # Lookup by human app_id
    res2 = client.get(f"/api/applications/{human_app_id}")
    assert res2.status_code == 200
    assert res2.json()["id"] == db_uuid


def test_repeat_analysis_idempotent(client, sample_pdf_path):
    """Verify re-running analysis on an application completes safely without duplicates."""
    app_id = _make_app(client, "Repeat Analysis College").json()["id"]
    with open(sample_pdf_path, "rb") as f:
        client.post(
            f"/api/applications/{app_id}/documents",
            files=[("files", ("doc.pdf", f, "application/pdf"))],
        )

    # First analysis run
    res1 = client.post(f"/api/applications/{app_id}/analyze")
    assert res1.status_code == 200
    fields_count_1 = len(res1.json()["extracted_fields"])

    # Second analysis run
    res2 = client.post(f"/api/applications/{app_id}/analyze")
    assert res2.status_code == 200
    fields_count_2 = len(res2.json()["extracted_fields"])

    # Field count should remain consistent (idempotent overwrite, no runaway growth)
    assert fields_count_1 == fields_count_2


# ── PDF Report ────────────────────────────────────────────────────────────────

def test_get_report(client, sample_pdf_path):
    """Verify PDF report is generated and returned with correct content-type."""
    app_id = _make_app(client, "Report Download College").json()["id"]
    with open(sample_pdf_path, "rb") as f:
        client.post(
            f"/api/applications/{app_id}/documents",
            files=[("files", ("doc.pdf", f, "application/pdf"))],
        )
    client.post(f"/api/applications/{app_id}/analyze")
    response = client.get(f"/api/applications/{app_id}/report")
    assert response.status_code == 200
    assert "pdf" in response.headers.get("content-type", "").lower()
    assert len(response.content) > 100  # Non-empty PDF bytes

