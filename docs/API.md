# TrustLens REST API Specification

> **Base URL**: `http://localhost:8000/api`  
> **API Version**: `v1.0-mvp`  
> **Interactive Swagger UI**: `http://localhost:8000/docs`  
> **ReDoc**: `http://localhost:8000/redoc`  

---

## 🔒 Authentication & Authorization Note

For the Smart India Hackathon MVP prototype, the API operates in an open local development environment without API keys or JWT tokens. All requests can be issued directly without `Authorization` headers.

In production:
- Role-Based Access Control (RBAC) will enforce roles: `SCRUTINY_OFFICER`, `REGIONAL_DIRECTOR`, `ADMINISTRATOR`, and `AUDITOR`.
- JWT Bearer tokens will authenticate requests via AICTE SSO / Parichay portal integration.

---

## ⚠️ Standard Error Response Format

All error responses return standard HTTP status codes (4xx/5xx) with a JSON body matching:

```json
{
  "detail": "Detailed, human-readable error description"
}
```

Common status codes:
- `400 Bad Request` – Missing required parameters, invalid file type, or malformed payload.
- `404 Not Found` – Requested application, document, or finding ID does not exist.
- `413 Payload Too Large` – Uploaded file exceeds the 35 MB size limit.
- `422 Unprocessable Entity` – Validation failure against Pydantic schema.
- `500 Internal Server Error` – Unhandled server or processing exception.

---

## 📋 Endpoint Index

1. [`GET /api/health`](#1-get-apihealth) — System health and dependency status
2. [`POST /api/applications`](#2-post-apiapplications) — Create an application dossier
3. [`GET /api/applications`](#3-get-apiapplications) — List all applications with summary metrics
4. [`GET /api/applications/{application_id}`](#4-get-apiapplicationsapplication_id) — Retrieve application details and documents
5. [`POST /api/applications/{application_id}/documents`](#5-post-apiapplicationsapplication_iddocuments) — Upload documents to an application
6. [`POST /api/applications/{application_id}/analyze`](#6-post-apiapplicationsapplication_idanalyze) — Run automated scrutiny analysis
7. [`GET /api/applications/{application_id}/findings`](#7-get-apiapplicationsapplication_idfindings) — Retrieve extracted fields and findings
8. [`POST /api/applications/{application_id}/findings/{finding_id}/review`](#8-post-apiapplicationsapplication_idfindingsfinding_idreview) — Submit officer review on a finding
9. [`GET /api/applications/{application_id}/report`](#9-get-apiapplicationsapplication_idreport) — Generate & download scrutiny PDF report
10. [`GET /api/applications/{application_id}/audit-trail`](#10-get-apiapplicationsapplication_idaudit-trail) — Retrieve cryptographic audit trail

---

## 1. `GET /api/health`

### Description
Checks server uptime and validates external dependencies including SQLite database connectivity, upload directory write permissions, and Tesseract OCR binary availability.

### Request
- **Method**: `GET`
- **Path**: `/api/health`
- **Headers**: None
- **Body**: None

### Response (`200 OK`)
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-10-26T14:30:00Z",
  "dependencies": {
    "database": "connected",
    "storage": "writable",
    "tesseract_ocr": "available"
  }
}
```

### Example `curl`
```bash
curl -X GET "http://localhost:8000/api/health" -H "Accept: application/json"
```

### Errors
- `503 Service Unavailable`: Critical dependency failed (e.g., SQLite database file unwritable).

---

## 2. `POST /api/applications`

### Description
Registers a new institutional scrutiny application file. Initializes metadata, creates database entry, and sets initial status to `PENDING_UPLOAD`.

### Request
- **Method**: `POST`
- **Path**: `/api/applications`
- **Headers**: `Content-Type: application/json`
- **Body Schema**:
```json
{
  "application_number": "string (required, e.g. 'AICTE-2024-VEC-001')",
  "institution_name": "string (required, e.g. 'Vigyan Engineering College')",
  "academic_year": "string (optional, default: '2024-2025')",
  "submitted_by": "string (optional, e.g. 'Dr. Priya Sharma')"
}
```

### Response (`201 Created`)
```json
{
  "id": "app_c91a0b38",
  "application_number": "AICTE-2024-VEC-001",
  "institution_name": "Vigyan Engineering College",
  "academic_year": "2024-2025",
  "status": "PENDING_UPLOAD",
  "risk_score": 0.0,
  "risk_level": "UNASSESSED",
  "document_count": 0,
  "created_at": "2024-10-26T14:32:00Z",
  "updated_at": "2024-10-26T14:32:00Z"
}
```

### Example `curl`
```bash
curl -X POST "http://localhost:8000/api/applications" \
  -H "Content-Type: application/json" \
  -d '{
    "application_number": "AICTE-2024-VEC-001",
    "institution_name": "Vigyan Engineering College",
    "academic_year": "2024-2025",
    "submitted_by": "Dr. Priya Sharma"
  }'
```

### Errors
- `400 Bad Request`: `application_number` or `institution_name` missing or invalid format.
- `409 Conflict`: Application with the given `application_number` already exists.

---

## 3. `GET /api/applications`

### Description
Lists all applications in the system with summary status, risk score, risk level, and document count. Supports optional search and status filtering.

### Request
- **Method**: `GET`
- **Path**: `/api/applications`
- **Query Parameters**:
  - `status` *(string, optional)*: Filter by status (e.g. `PENDING_UPLOAD`, `ANALYZED`, `REVIEWED`).
  - `search` *(string, optional)*: Partial match on institution name or application number.
  - `limit` *(integer, optional, default: 50)*: Number of records to return.
  - `offset` *(integer, optional, default: 0)*: Pagination offset.

### Response (`200 OK`)
```json
{
  "total": 1,
  "limit": 50,
  "offset": 0,
  "items": [
    {
      "id": "app_c91a0b38",
      "application_number": "AICTE-2024-VEC-001",
      "institution_name": "Vigyan Engineering College",
      "academic_year": "2024-2025",
      "status": "ANALYZED",
      "risk_score": 12.5,
      "risk_level": "LOW",
      "document_count": 3,
      "findings_summary": {
        "critical": 0,
        "warning": 1,
        "info": 4
      },
      "created_at": "2024-10-26T14:32:00Z"
    }
  ]
}
```

### Example `curl`
```bash
curl -X GET "http://localhost:8000/api/applications?limit=10" -H "Accept: application/json"
```

---

## 4. `GET /api/applications/{application_id}`

### Description
Fetches comprehensive details for a specific application, including associated documents, current analysis state, advisory risk score, and officer review summary.

### Request
- **Method**: `GET`
- **Path**: `/api/applications/{application_id}`
- **Path Parameters**:
  - `application_id` *(string, required)*: Unique identifier of the application.

### Response (`200 OK`)
```json
{
  "id": "app_c91a0b38",
  "application_number": "AICTE-2024-VEC-001",
  "institution_name": "Vigyan Engineering College",
  "academic_year": "2024-2025",
  "status": "ANALYZED",
  "risk_score": 12.5,
  "risk_level": "LOW",
  "created_at": "2024-10-26T14:32:00Z",
  "updated_at": "2024-10-26T14:35:10Z",
  "documents": [
    {
      "id": "doc_8f14b2d1",
      "filename": "sample_01_complete.pdf",
      "file_type": "application/pdf",
      "file_size": 18432,
      "sha256": "8f3b...4c9a",
      "phash": "a7c3...12e4",
      "ocr_status": "COMPLETED",
      "uploaded_at": "2024-10-26T14:33:00Z"
    }
  ]
}
```

### Example `curl`
```bash
curl -X GET "http://localhost:8000/api/applications/app_c91a0b38"
```

### Errors
- `404 Not Found`: Application ID not found.

---

## 5. `POST /api/applications/{application_id}/documents`

### Description
Uploads one or more verification documents (PDF, PNG, JPG, JPEG, TIFF) to the application dossier. Performs format validation, computes SHA-256 and pHash fingerprints, and saves files to the upload repository.

### Request
- **Method**: `POST`
- **Path**: `/api/applications/{application_id}/documents`
- **Headers**: `Content-Type: multipart/form-data`
- **Path Parameters**:
  - `application_id` *(string, required)*: Unique application identifier.
- **Form Data**:
  - `files` *(binary file(s), required)*: Document file(s) to upload.
  - `document_type` *(string, optional)*: Classification hint (e.g., `AFFILIATION_CERTIFICATE`, `LAND_RECORD`, `INSPECTION_REPORT`).

### Response (`201 Created`)
```json
{
  "application_id": "app_c91a0b38",
  "uploaded_count": 2,
  "documents": [
    {
      "id": "doc_8f14b2d1",
      "filename": "sample_01_complete.pdf",
      "file_size": 18432,
      "sha256": "8f3b20d1c8...a5e6",
      "phash": "f0e0c0808080c0f0",
      "status": "UPLOADED"
    },
    {
      "id": "doc_9e25c3f2",
      "filename": "sample_04a_duplicate.png",
      "file_size": 24510,
      "sha256": "d41d8cd98f...0001",
      "phash": "ffff0000ffff0000",
      "status": "UPLOADED"
    }
  ]
}
```

### Example `curl`
```bash
curl -X POST "http://localhost:8000/api/applications/app_c91a0b38/documents" \
  -F "files=@sample_01_complete.pdf" \
  -F "files=@sample_04a_duplicate.png"
```

### Errors
- `400 Bad Request`: Unsupported file type (e.g. `.exe`, `.docx`) or zero-byte file.
- `404 Not Found`: Application not found.
- `413 Payload Too Large`: Total upload payload exceeds 35MB.

---

## 6. `POST /api/applications/{application_id}/analyze`

### Description
Triggers the asynchronous/synchronous automated scrutiny analysis pipeline:
1. PyMuPDF digital text extraction + Tesseract OCR fallback on all documents.
2. Regex-based structured metadata extraction (Institution, App No, Address, Director, Intake, Affiliation).
3. Hash-based exact duplicate detection and perceptual hash matching against application and repository.
4. Cross-document comparison flagging inconsistencies across files in the dossier.
5. Error-Level Analysis (ELA) inspection on image documents.
6. Rule Engine evaluation against `rules.json` compliance policies.
7. Calculation of transparent advisory risk score (0–100).
8. Logging event to cryptographic audit trail.

### Request
- **Method**: `POST`
- **Path**: `/api/applications/{application_id}/analyze`
- **Path Parameters**:
  - `application_id` *(string, required)*: Unique application identifier.
- **Body**: None

### Response (`200 OK`)
```json
{
  "application_id": "app_c91a0b38",
  "status": "ANALYZED",
  "duration_seconds": 2.45,
  "documents_processed": 2,
  "risk_score": 15.0,
  "risk_level": "LOW",
  "total_findings": 3,
  "findings_breakdown": {
    "critical": 0,
    "warning": 1,
    "info": 2
  },
  "message": "Analysis completed successfully. Findings ready for officer review."
}
```

### Example `curl`
```bash
curl -X POST "http://localhost:8000/api/applications/app_c91a0b38/analyze"
```

### Errors
- `400 Bad Request`: Application has no uploaded documents to analyze.
- `404 Not Found`: Application not found.
- `500 Internal Server Error`: Processing pipeline failure.

---

## 7. `GET /api/applications/{application_id}/findings`

### Description
Returns all extracted structured metadata and findings (rule violations, cross-document mismatches, duplicates, and tampering alerts) generated by the analysis pipeline.

### Request
- **Method**: `GET`
- **Path**: `/api/applications/{application_id}/findings`
- **Path Parameters**:
  - `application_id` *(string, required)*: Unique application identifier.

### Response (`200 OK`)
```json
{
  "application_id": "app_c91a0b38",
  "risk_score": 45.0,
  "risk_level": "MEDIUM",
  "extracted_fields": [
    {
      "field_name": "institution_name",
      "value": "ABC Technical Institute",
      "confidence": 0.95,
      "source_document_id": "doc_02a",
      "source_filename": "sample_02a_mismatch.pdf"
    },
    {
      "field_name": "institution_name",
      "value": "XYZ Technology College",
      "confidence": 0.94,
      "source_document_id": "doc_02b",
      "source_filename": "sample_02b_mismatch.pdf"
    }
  ],
  "findings": [
    {
      "id": "fnd_7a12e340",
      "category": "CROSS_DOCUMENT_MISMATCH",
      "severity": "CRITICAL",
      "rule_id": "RULE_CROSSDOC_NAME_MATCH",
      "title": "Discrepancy in Institution Name across documents",
      "description": "Document sample_02a specifies 'ABC Technical Institute' while sample_02b specifies 'XYZ Technology College' for Application AICTE-2024-ABC-002.",
      "risk_weight": 35,
      "status": "OPEN",
      "evidence": {
        "doc_a": "sample_02a_mismatch.pdf",
        "value_a": "ABC Technical Institute",
        "doc_b": "sample_02b_mismatch.pdf",
        "value_b": "XYZ Technology College"
      },
      "review": null
    }
  ]
}
```

### Example `curl`
```bash
curl -X GET "http://localhost:8000/api/applications/app_c91a0b38/findings"
```

### Errors
- `404 Not Found`: Application not found.

---

## 8. `POST /api/applications/{application_id}/findings/{finding_id}/review`

### Description
Records a human scrutiny officer review decision on an individual finding. The officer can accept the finding (validating the violation), reject it (marking it as a false alarm), or override it with justification. Recalculates the effective risk score and commits an entry to the audit log.

### Request
- **Method**: `POST`
- **Path**: `/api/applications/{application_id}/findings/{finding_id}/review`
- **Headers**: `Content-Type: application/json`
- **Path Parameters**:
  - `application_id` *(string, required)*: Unique application identifier.
  - `finding_id` *(string, required)*: Unique finding identifier.
- **Body Schema**:
```json
{
  "action": "string (required, enum: ['ACCEPTED', 'REJECTED', 'OVERRIDDEN'])",
  "officer_name": "string (required, e.g. 'Officer S. K. Raman')",
  "officer_id": "string (optional, e.g. 'OFFICER-4091')",
  "comments": "string (required, explanation of officer determination)"
}
```

### Response (`200 OK`)
```json
{
  "finding_id": "fnd_7a12e340",
  "action": "ACCEPTED",
  "status": "REVIEWED",
  "reviewed_by": "Officer S. K. Raman",
  "reviewed_at": "2024-10-26T14:40:00Z",
  "comments": "Verified mismatch between title deed and application form. Formal clarification required from applicant.",
  "application_risk_score": 45.0,
  "audit_entry_id": "aud_01f928"
}
```

### Example `curl`
```bash
curl -X POST "http://localhost:8000/api/applications/app_c91a0b38/findings/fnd_7a12e340/review" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "ACCEPTED",
    "officer_name": "Officer S. K. Raman",
    "comments": "Verified mismatch between title deed and application form. Formal clarification required from applicant."
  }'
```

### Errors
- `400 Bad Request`: Invalid action enum or empty comment text.
- `404 Not Found`: Application or finding ID not found.

---

## 9. `GET /api/applications/{application_id}/report`

### Description
Generates and downloads a complete, publication-grade multi-page Scrutiny Dossier PDF report using ReportLab. The report includes application summary, extracted fields, all rule evaluations, officer review notes, risk score gauge, and cryptographic audit hash.

### Request
- **Method**: `GET`
- **Path**: `/api/applications/{application_id}/report`
- **Path Parameters**:
  - `application_id` *(string, required)*: Unique application identifier.

### Response (`200 OK`)
- **Content-Type**: `application/pdf`
- **Content-Disposition**: `attachment; filename="AICTE_Scrutiny_Report_AICTE-2024-VEC-001.pdf"`
- **Body**: Binary PDF stream.

### Example `curl`
```bash
curl -X GET "http://localhost:8000/api/applications/app_c91a0b38/report" \
  --output "Scrutiny_Report.pdf"
```

### Errors
- `400 Bad Request`: Application has not been analyzed yet.
- `404 Not Found`: Application ID not found.

---

## 10. `GET /api/applications/{application_id}/audit-trail`

### Description
Fetches the immutable, tamper-evident hash-chained audit log for the application. Each event includes previous block hash, event payload hash, timestamp, actor ID, action type, and details.

### Request
- **Method**: `GET`
- **Path**: `/api/applications/{application_id}/audit-trail`
- **Path Parameters**:
  - `application_id` *(string, required)*: Unique application identifier.

### Response (`200 OK`)
```json
{
  "application_id": "app_c91a0b38",
  "is_chain_valid": true,
  "total_events": 3,
  "events": [
    {
      "sequence": 1,
      "event_type": "APPLICATION_CREATED",
      "actor": "Dr. Priya Sharma",
      "timestamp": "2024-10-26T14:32:00Z",
      "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000",
      "block_hash": "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
      "details": { "application_number": "AICTE-2024-VEC-001" }
    },
    {
      "sequence": 2,
      "event_type": "ANALYSIS_COMPLETED",
      "actor": "TrustLens_Pipeline",
      "timestamp": "2024-10-26T14:35:10Z",
      "prev_hash": "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
      "block_hash": "b2c3d4e5f6a10718293a4b5c6d7e8f90123456789abcdef0123456789abcdef1",
      "details": { "risk_score": 12.5, "findings_count": 3 }
    },
    {
      "sequence": 3,
      "event_type": "OFFICER_REVIEW_SUBMITTED",
      "actor": "Officer S. K. Raman",
      "timestamp": "2024-10-26T14:40:00Z",
      "prev_hash": "b2c3d4e5f6a10718293a4b5c6d7e8f90123456789abcdef0123456789abcdef1",
      "block_hash": "c3d4e5f6a1b20718293a4b5c6d7e8f90123456789abcdef0123456789abcdef2",
      "details": { "finding_id": "fnd_7a12e340", "action": "ACCEPTED" }
    }
  ]
}
```

### Example `curl`
```bash
curl -X GET "http://localhost:8000/api/applications/app_c91a0b38/audit-trail"
```

### Errors
- `404 Not Found`: Application ID not found.
