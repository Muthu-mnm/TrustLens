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

def test_review_finding(client, sample_pdf_path):
    """Verify officer can review a finding and it persists."""
    app_id = _make_app(client, "Review Action College").json()["id"]
    with open(sample_pdf_path, "rb") as f:
        client.post(
            f"/api/applications/{app_id}/documents",
            files=[("files", ("doc.pdf", f, "application/pdf"))],
        )
    analysis = client.post(f"/api/applications/{app_id}/analyze").json()
    findings = analysis.get("findings", [])

    if not findings:
        pytest.skip("No findings generated for review test - document may be complete")

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


def test_review_invalid_status(client, sample_pdf_path):
    """Verify invalid review status returns 400."""
    app_id = _make_app(client, "Invalid Review College").json()["id"]
    with open(sample_pdf_path, "rb") as f:
        client.post(
            f"/api/applications/{app_id}/documents",
            files=[("files", ("doc.pdf", f, "application/pdf"))],
        )
    analysis = client.post(f"/api/applications/{app_id}/analyze").json()
    findings = analysis.get("findings", [])
    if not findings:
        pytest.skip("No findings to test invalid review")

    finding_id = findings[0]["id"]
    res = client.post(
        f"/api/findings/{finding_id}/review",
        json={"review_status": "approved_by_ai", "reviewed_by": "Bot"},
    )
    assert res.status_code == 400


# ── Audit Trail ───────────────────────────────────────────────────────────────

def test_get_audit(client):
    """Verify audit trail is populated after application creation."""
    app_id = _make_app(client, "Audit Trail Test College").json()["id"]
    response = client.get(f"/api/applications/{app_id}/audit")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At minimum APPLICATION_CREATED entry
    assert data[0]["action"] == "APPLICATION_CREATED"


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
