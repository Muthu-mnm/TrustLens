# TrustLens Architecture & System Design Document

> **System**: TrustLens – Explainable AI Decision-Support for AICTE Application Scrutiny  
> **Hackathon**: Smart India Hackathon (SIH) 2024  
> **Problem Statement**: SIH26261 (V-Matrix)  
> **Design Version**: 1.0.0-MVP  

---

## 1. System Architecture Overview

TrustLens is architected as a decoupled, micro-modular client-server system designed for high explainability, auditability, and speed. The system empowers AICTE scrutiny officers with automated document verification while strictly maintaining human authority over all final regulatory determinations.

### ASCII Architecture Diagram

```
+-------------------------------------------------------------------------------------------------------------------+
|                                                 PRESENTATION TIER                                                 |
|                                                                                                                   |
|                               +----------------------------------------------------+                              |
|                               |             Scrutiny Officer Browser               |                              |
|                               +----------------------------------------------------+                              |
|                                                         |                                                         |
|                                                         v                                                         |
|                               +----------------------------------------------------+                              |
|                               |             React 18 + Vite Frontend               |                              |
|                               |  - Tailwind CSS Glassmorphic UI  - State Store     |                              |
|                               |  - Scrutiny Dashboard            - Findings Review |                              |
|                               |  - Risk Score Gauge UI           - Audit Viewer    |                              |
|                               +----------------------------------------------------+                              |
+---------------------------------------------------------|---------------------------------------------------------+
                                                          | HTTP REST (JSON / Multipart)
                                                          v
+-------------------------------------------------------------------------------------------------------------------+
|                                                  APPLICATION TIER                                                 |
|                                                                                                                   |
|                                        FastAPI Backend Application (Port: 8000)                                   |
|                                                                                                                   |
|   +-----------------------------------------------------------------------------------------------------------+   |
|   | API Router Layer                                                                                          |   |
|   |  - /api/health           - /api/applications          - /api/applications/{id}/documents                  |   |
|   |  - /api/analyze          - /api/findings              - /api/findings/{id}/review                         |   |
|   |  - /api/report           - /api/audit-trail                                                               |   |
|   +-----------------------------------------------------------------------------------------------------------+   |
|                                                          |                                                         |
|   +-----------------------------------------------------------------------------------------------------------+   |
|   | Core Analysis & Scrutiny Services                                                                         |   |
|   |                                                                                                           |   |
|   |   +--------------------------+  +--------------------------+  +---------------------------------------+   |   |
|   |   |        OCR Engine        |  |  Field Extraction Service|  |       Duplicate Detection Engine      |   |   |
|   |   | - PyMuPDF (native text)  |  | - Regex Entity Extractors|  | - SHA-256 Bitwise Cryptographic Hash  |   |   |
|   |   | - Tesseract OCR fallback |  | - Normalized Key Matcher |  | - ImageHash Perceptual Hash (pHash)   |   |   |
|   |   +--------------------------+  +--------------------------+  +---------------------------------------+   |   |
|   |                                                                                                           |   |
|   |   +--------------------------+  +--------------------------+  +---------------------------------------+   |   |
|   |   |  Error-Level Analysis    |  |  Cross-Doc Match Engine  |  |        Compliance Rule Engine         |   |   |
|   |   | - ELA Compression Delta  |  | - Entity Cross-Validator |  | - Deterministic Evaluator             |   |   |
|   |   | - Alteration Heuristic   |  | - Inconsistency Detector |  | - Config-driven via rules.json        |   |   |
|   |   +--------------------------+  +--------------------------+  +---------------------------------------+   |   |
|   |                                                                                                           |   |
|   |   +--------------------------------------------------------+  +---------------------------------------+   |   |
|   |   |              Advisory Risk Scoring Engine              |  |         ReportLab PDF Generator       |   |   |
|   |   | - Weighted Severity Model (Critical, High, Medium, Low)|  | - Executive Multi-page Scrutiny PDF   |   |   |
|   |   | - Explainable Risk Breakdown & Formula Explanation     |  | - Embedded Risk & Evidence Tables     |   |   |
|   |   +--------------------------------------------------------+  +---------------------------------------+   |   |
|   +-----------------------------------------------------------------------------------------------------------+   |
|                                                          |                                                         |
|   +-----------------------------------------------------------------------------------------------------------+   |
|   | Tamper-Evident Audit Service: Hash-chained sequential event log (SHA-256 block ledger)                   |   |
|   +-----------------------------------------------------------------------------------------------------------+   |
+---------------------------------------------------------|---------------------------------------------------------+
                                                          |
                                           +--------------+--------------+
                                           |                             |
                                           v                             v
+--------------------------------------------------+     +--------------------------------------------------+
|                  DATA STORAGE TIER               |     |                 FILE STORAGE TIER                |
|                                                  |     |                                                  |
|              SQLite Relational Database          |     |           Local Secure Upload Directory          |
|  - Applications table    - Documents table       |     |                 (backend/uploads/)               |
|  - ExtractedFields table - Findings table        |     |  - Raw submitted PDFs, PNGs, JPGs                |
|  - OfficerReviews table  - AuditLedger table     |     |  - Generated Scrutiny PDF reports                |
+--------------------------------------------------+     +--------------------------------------------------+
```

---

## 2. End-to-End Analysis Pipeline Data Flow

When a scrutiny officer clicks **"Run Analysis"** for an application dossier, the following sequential pipeline executes:

```
[Uploaded Docs]
       |
       v
+---------------------------------------------------------------------------------------------+
| Stage 1: Ingestion & Fingerprinting                                                         |
|  - Compute SHA-256 binary hash (for exact duplicates).                                      |
|  - Generate 64-bit perceptual hash (pHash) via ImageHash (for resized/scanned duplicates).  |
|  - Check hashes against existing records in SQLite and current dossier.                     |
+---------------------------------------------------------------------------------------------+
       |
       v
+---------------------------------------------------------------------------------------------+
| Stage 2: Dual-Stream OCR & Text Normalization                                               |
|  - If PDF: Attempt direct vector text extraction via PyMuPDF (fitz) for pristine speed.     |
|  - If image or raster-only PDF: Rasterize page at 300 DPI and run Tesseract OCR.            |
|  - Normalize extracted text: strip whitespace, fix OCR ligature artifacts, build corpus.    |
+---------------------------------------------------------------------------------------------+
       |
       v
+---------------------------------------------------------------------------------------------+
| Stage 3: Structured Field Extraction                                                        |
|  - Execute specialized regex and positional heuristics for key AICTE fields:                |
|    * Application Number, Institution Name, Address & State, Director/Principal Name,        |
|    * Phone, Email, Year of Establishment, Affiliating University, Sanctioned Intake,        |
|    * Program List (B.Tech, M.Tech, Diploma).                                                |
|  - Assign confidence score (0.00 – 1.00) based on pattern matching reliability.             |
+---------------------------------------------------------------------------------------------+
       |
       v
+---------------------------------------------------------------------------------------------+
| Stage 4: Cross-Document Consistency Analysis                                                |
|  - Group extracted fields by field name across all documents in the application dossier.    |
|  - If `Institution Name` or `Application No` differs between Document A and Document B,     |
|    emit `CRITICAL_MISMATCH` finding with side-by-side evidence strings.                     |
+---------------------------------------------------------------------------------------------+
       |
       v
+---------------------------------------------------------------------------------------------+
| Stage 5: Forensic Image Tampering Inspection (ELA)                                          |
|  - For image submissions: Resave image at 90% JPEG quality, compute absolute pixel delta,   |
|    scale brightness, and calculate mean error difference across blocks.                     |
|  - If local error variance exceeds statistical threshold, flag advisory ELA anomaly.        |
+---------------------------------------------------------------------------------------------+
       |
       v
+---------------------------------------------------------------------------------------------+
| Stage 6: Rule Engine Compliance Evaluation                                                  |
|  - Evaluate extracted metadata against configured regulatory rules (`rules.json`):         |
|    * MANDATORY_FIELDS_CHECK: Flags missing mandatory fields (Name, Email, Address, etc.).   |
|    * INTAKE_THRESHOLD_CHECK: Flags intake exceeding handbook limits without approvals.      |
|    * VALID_EMAIL_FORMAT: Flags non-institutional or invalid domain email patterns.         |
|    * PHONE_FORMAT_CHECK: Flags invalid telecommunication formats.                          |
+---------------------------------------------------------------------------------------------+
       |
       v
+---------------------------------------------------------------------------------------------+
| Stage 7: Advisory Risk Score Calculation                                                    |
|  - Aggregate severity weights: Critical (+35), High (+20), Medium (+10), Low (+5).          |
|  - Apply saturation curve: RiskScore = min(100, Sum(Weights)).                              |
|  - Classify Risk Level: Low (0-29), Medium (30-69), High (70-100).                           |
+---------------------------------------------------------------------------------------------+
       |
       v
+---------------------------------------------------------------------------------------------+
| Stage 8: Audit Log Chaining & Persistence                                                   |
|  - Store all findings and extracted fields in SQLite.                                       |
|  - Compute SHA-256 block hash chaining `[prev_hash + timestamp + event_payload]`.            |
|  - Update application state to `ANALYZED`. Ready for officer review.                       |
+---------------------------------------------------------------------------------------------+
```

---

## 3. Component Descriptions

### 3.1 Presentation Layer (Frontend)
- **Framework**: React 18, bundled with Vite for near-instant HMR.
- **Styling**: Vanilla CSS custom variables combined with Tailwind CSS utility architecture for clean glassmorphism and modern dark/light contrast.
- **Key Modules**:
  - `ApplicationList`: Overview table with search, status filters, and risk badges.
  - `ApplicationWorkspace`: Tabbed scrutinizing view (Overview, Documents, Extracted Fields, Compliance Findings, Tampering ELA, Audit Trail).
  - `RiskScoreGauge`: Interactive SVG gauge depicting the explainable risk level.
  - `OfficerReviewModal`: Granular per-finding review dialog with justification input.

### 3.2 API Layer (FastAPI Backend)
- **Framework**: FastAPI (Python 3.10+) running under Uvicorn ASGI server.
- **Validation**: Pydantic v2 data models for strict schema validation.
- **CORS Handling**: Fast, asynchronous CORS middleware for local frontend communication.

### 3.3 Core Processing Services
- **OCR Service (`ocr_service.py`)**: Dual-engine extraction prioritizing digital vector streams via PyMuPDF, falling back to pytesseract for rasterized images.
- **Extraction Service (`extraction_service.py`)**: Regular expression engine matching AICTE institutional parameters with confidence metrics.
- **Duplicate Service (`duplicate_service.py`)**: Computes SHA-256 for exact bitwise matches and 64-bit dhash/phash for perceptual visual matches.
- **ELA Service (`ela_service.py`)**: Error-Level Analysis determining recompression variance to highlight edited or erased document regions.
- **Rule Engine (`rule_engine.py`)**: Configurable evaluator loading business rules from `rules.json` to keep scrutiny policies agile and auditable.
- **Scoring Service (`scoring_service.py`)**: Calculates deterministic risk scores with human-readable rationale.
- **Audit Service (`audit_service.py`)**: Sequential block ledger maintaining immutable audit trails.
- **Report Service (`report_service.py`)**: ReportLab document builder exporting multi-page PDF scrutiny dossiers.

---

## 4. Technology Stack & Justification

| Layer / Library | Selected Tech | Justification for AICTE Scrutiny MVP |
|---|---|---|
| **Frontend Framework** | **React 18 + Vite** | Instant cold start, reactive component state, widespread team familiarity. |
| **Styling** | **Tailwind CSS** | Rapid UI development, uniform design system tokens, responsive glassmorphism. |
| **Backend Framework** | **FastAPI** | High throughput async Python, auto-generated OpenAPI/Swagger, strict Pydantic validation. |
| **Database** | **SQLite (via SQLAlchemy/aiosqlite)** | Zero-config, serverless, self-contained single file storage ideal for hackathon MVP demo. |
| **PDF Text Extraction** | **PyMuPDF (`fitz`)** | Up to 10x faster than traditional PDF parsers; preserves text coordinates accurately. |
| **OCR Engine** | **Tesseract OCR (5.x)** | Open-source, battle-tested OCR engine supporting scanned text and multiple languages. |
| **Image Processing** | **Pillow (`PIL`)** | Universal Python imaging library for ELA, pixel diffing, and image conversions. |
| **Perceptual Hashing**| **ImageHash** | Robust detection of resized, rotated, or re-compressed duplicate documents. |
| **PDF Generation** | **ReportLab** | Enterprise-grade PDF compilation engine with precise typography and layout controls. |
| **Testing** | **Pytest** | Standard Python testing framework for unit and integration endpoint validation. |

---

## 5. Text-Based Database ERD

```
+-----------------------------------------------------------------------------------------+
|                                      APPLICATIONS                                       |
+-----------------------------------------------------------------------------------------+
| * id: VARCHAR(36) [PK]              -- UUID primary key                                 |
|   application_number: VARCHAR(64)   -- e.g. 'AICTE-2024-VEC-001' [UNIQUE]               |
|   institution_name: VARCHAR(255)    -- Registered college name                          |
|   academic_year: VARCHAR(16)        -- e.g. '2024-2025'                                 |
|   submitted_by: VARCHAR(128)        -- Submitter or applicant name                      |
|   status: VARCHAR(32)               -- PENDING_UPLOAD, UPLOADED, ANALYZED, REVIEWED     |
|   risk_score: FLOAT                 -- Advisory score 0.0 to 100.0                      |
|   risk_level: VARCHAR(16)           -- LOW, MEDIUM, HIGH                                |
|   created_at: DATETIME              -- Timestamp                                        |
|   updated_at: DATETIME              -- Timestamp                                        |
+-----------------------------------------------------------------------------------------+
          | 1
          |
          | N
+-----------------------------------------------------------------------------------------+
|                                        DOCUMENTS                                        |
+-----------------------------------------------------------------------------------------+
| * id: VARCHAR(36) [PK]              -- UUID primary key                                 |
|   application_id: VARCHAR(36) [FK]  -- References APPLICATIONS(id)                      |
|   filename: VARCHAR(255)            -- Stored file name                                 |
|   original_name: VARCHAR(255)       -- Uploaded file name                               |
|   file_path: VARCHAR(512)           -- Relative filesystem path in uploads/             |
|   file_type: VARCHAR(64)            -- MIME type (application/pdf, image/png)           |
|   file_size: INTEGER                -- Size in bytes                                    |
|   sha256: VARCHAR(64)               -- SHA-256 cryptographic checksum                   |
|   phash: VARCHAR(64)                -- Perceptual hash string                           |
|   ocr_text: TEXT                    -- Raw extracted OCR text                           |
|   created_at: DATETIME              -- Timestamp                                        |
+-----------------------------------------------------------------------------------------+
          | 1
          |
          | N
+-----------------------------------------------------------------------------------------+
|                                    EXTRACTED_FIELDS                                     |
+-----------------------------------------------------------------------------------------+
| * id: VARCHAR(36) [PK]              -- UUID primary key                                 |
|   document_id: VARCHAR(36) [FK]     -- References DOCUMENTS(id)                         |
|   application_id: VARCHAR(36) [FK]  -- References APPLICATIONS(id)                      |
|   field_name: VARCHAR(64)           -- e.g. 'institution_name', 'director', 'intake'    |
|   field_value: TEXT                 -- Extracted text value                             |
|   confidence: FLOAT                 -- Confidence score (0.00 - 1.00)                   |
|   raw_snippet: TEXT                 -- Text snippet containing match                    |
|   created_at: DATETIME              -- Timestamp                                        |
+-----------------------------------------------------------------------------------------+

          | 1 (From Application)
          |
          | N
+-----------------------------------------------------------------------------------------+
|                                        FINDINGS                                         |
+-----------------------------------------------------------------------------------------+
| * id: VARCHAR(36) [PK]              -- UUID primary key                                 |
|   application_id: VARCHAR(36) [FK]  -- References APPLICATIONS(id)                      |
|   rule_id: VARCHAR(64)              -- e.g. 'RULE_CROSSDOC_NAME_MATCH'                  |
|   category: VARCHAR(64)             -- MISMATCH, DUPLICATE, MISSING_FIELD, TAMPERING    |
|   severity: VARCHAR(16)             -- CRITICAL, WARNING, INFO                          |
|   title: VARCHAR(255)               -- Short summary of issue                           |
|   description: TEXT                 -- Detailed explanation and context                 |
|   risk_weight: INTEGER              -- Numerical weight added to score                  |
|   status: VARCHAR(32)               -- OPEN, ACCEPTED, REJECTED, OVERRIDDEN             |
|   evidence_json: TEXT               -- Structured JSON containing documents & values    |
|   created_at: DATETIME              -- Timestamp                                        |
+-----------------------------------------------------------------------------------------+
          | 1
          |
          | 0..1
+-----------------------------------------------------------------------------------------+
|                                     OFFICER_REVIEWS                                     |
+-----------------------------------------------------------------------------------------+
| * id: VARCHAR(36) [PK]              -- UUID primary key                                 |
|   finding_id: VARCHAR(36) [FK]      -- References FINDINGS(id)                          |
|   officer_name: VARCHAR(128)        -- Name of reviewing scrutiny officer               |
|   officer_id: VARCHAR(64)           -- Badge or Officer ID                              |
|   action: VARCHAR(32)               -- ACCEPTED, REJECTED, OVERRIDDEN                   |
|   comments: TEXT                    -- Regulatory justification and observations        |
|   created_at: DATETIME              -- Timestamp of review                              |
+-----------------------------------------------------------------------------------------+

          | 1 (From Application)
          |
          | N
+-----------------------------------------------------------------------------------------+
|                                      AUDIT_LEDGER                                       |
+-----------------------------------------------------------------------------------------+
| * id: VARCHAR(36) [PK]              -- UUID primary key                                 |
|   application_id: VARCHAR(36) [FK]  -- References APPLICATIONS(id)                      |
|   sequence: INTEGER                 -- Monotonically increasing event index (1, 2, 3...) |
|   event_type: VARCHAR(64)           -- APPLICATION_CREATED, ANALYZED, REVIEWED...       |
|   actor: VARCHAR(128)               -- Officer name or automated subsystem              |
|   timestamp: DATETIME               -- ISO timestamp                                    |
|   prev_hash: VARCHAR(64)            -- SHA-256 of preceding audit record                |
|   block_hash: VARCHAR(64)           -- SHA-256 of current record payload + prev_hash    |
|   details_json: TEXT                -- Event metadata and state snapshot                |
+-----------------------------------------------------------------------------------------+
```

---

## 6. Team Task Allocation (5 Members)

| Member | Role | Primary Files & Responsibilities |
|---|---|---|
| **Member 1** | **React Frontend** | `frontend/src/pages/*`, `frontend/src/components/*`<br>• Application dashboard & status lists<br>• Document upload zone with drag-and-drop<br>• Visual findings inspector & risk score gauge<br>• Officer review modal & audit trail timeline view |
| **Member 2** | **OCR & Extraction** | `app/services/ocr_service.py`, `app/services/extraction_service.py`<br>• PyMuPDF text stream extraction<br>• Tesseract OCR raster pipeline<br>• Regex entity extractors (Name, App No, Address, Intake)<br>• OCR confidence evaluation heuristics |
| **Member 3** | **CV & Duplicate Detection** | `app/services/duplicate_service.py`, `app/services/ela_service.py`<br>• SHA-256 exact document deduplication<br>• ImageHash perceptual pHash comparison<br>• Error-Level Analysis (ELA) re-compression diffing<br>• Visual alteration heatmap generation |
| **Member 4** | **Rule Engine & Scoring** | `app/services/rule_engine.py`, `app/services/scoring_service.py`, `app/config/rules.json`<br>• Configurable JSON rule definitions<br>• Cross-document mismatch evaluator<br>• Missing mandatory field validator<br>• Weighted advisory risk score formula |
| **Member 5** | **Backend Integration** | `app/main.py`, `app/routers/*`, `app/services/report_service.py`, `tests/*`<br>• FastAPI router setup and CORS configuration<br>• SQLite database models and migrations<br>• ReportLab PDF Scrutiny Dossier generation<br>• Pytest test suite & API verification |

---

## 7. Seven-Day Hackathon Implementation Roadmap

```
Day 1: Foundation & Schemas
[All Members] Setup repo, dependencies, SQLite schemas, sample data specs.

Day 2: Ingestion & OCR Pipeline
[M2] PyMuPDF + Tesseract integration. [M3] SHA-256 + pHash hashing. [M1] Upload UI.

Day 3: Extraction & Cross-Doc Comparison
[M2] Regex entity extraction. [M4] Cross-document comparator. [M1] Metadata view.

Day 4: Rules, Scoring & Forensics
[M4] rules.json + scoring engine. [M3] ELA compression analysis. [M1] Findings UI.

Day 5: Review Controls & Audit Trail
[M5] Hash-chained audit ledger. [M1] Review modal. [M4] Risk score updates.

Day 6: PDF Report & Polish
[M5] ReportLab PDF dossier generation. [M1] Visual polish & dark mode. [M5] Tests.

Day 7: Rehearsal & Judge Demo
[All Members] Run generate_test_docs.py, execute demo script, prepare Q&A.
```

### Detailed Day-by-Day Milestone Checklist

- **Day 1: Project Initialization & Environment Setup**
  - [x] Create project repository structure (`backend/`, `frontend/`, `docs/`, `test_data/`).
  - [x] Configure Python virtual environment, Node dependencies, and `requirements.txt`.
  - [x] Implement `test_data/generate_test_docs.py` to generate 7 synthetic test documents.
  - [x] Scaffold FastAPI app with `/api/health` and SQLite DB schema.

- **Day 2: Document Ingestion, Storage & OCR**
  - [x] Build multipart upload endpoint `/api/applications/{id}/documents`.
  - [x] Implement PyMuPDF digital text reader and Tesseract OCR fallback for scanned images.
  - [x] Implement SHA-256 cryptographic hashing and perceptual pHash computation.
  - [x] Create React document upload zone with format validation.

- **Day 3: Structured Extraction & Cross-Document Comparison**
  - [x] Build regex extraction patterns for Institution Name, Application No, Director, Address, Intake.
  - [x] Implement cross-document comparator detecting inconsistencies across documents.
  - [x] Store extracted fields in SQLite with confidence scores.
  - [x] Create frontend "Extracted Fields" comparison table.

- **Day 4: Compliance Rule Engine & Risk Scoring**
  - [x] Implement `rules.json` with mandatory fields, intake limits, and phone/email checks.
  - [x] Build deterministic `RuleEngine` evaluating extracted fields against policies.
  - [x] Implement Error-Level Analysis (ELA) for image document tampering inspection.
  - [x] Create weighted advisory risk scoring engine (0–100) and frontend Risk Gauge.

- **Day 5: Officer Review System & Tamper-Evident Audit Trail**
  - [x] Implement `/api/findings/{id}/review` endpoint supporting `ACCEPT`, `REJECT`, `OVERRIDE`.
  - [x] Implement SHA-256 hash-chained `AuditLedger` logging all state transitions.
  - [x] Build frontend Officer Review modal and interactive Audit Trail viewer.
  - [x] Ensure risk scores update dynamically upon officer reviews.

- **Day 6: ReportLab PDF Report Export & Integration Testing**
  - [x] Implement `report_service.py` generating official AICTE Scrutiny Dossier PDF.
  - [x] Build complete Pytest test suite (`tests/test_api.py`, `tests/test_ocr.py`, `tests/test_rules.py`).
  - [x] Finalize frontend UI responsiveness, error handling, and toast alerts.

- **Day 7: Demo Rehearsal & Presentation Readiness**
  - [x] Validate all 7 synthetic sample scenarios using `DEMO_SCRIPT.md`.
  - [x] Review anticipated judge questions and practice verbal explanations.
  - [x] Verify offline fallback capabilities in case of local network disruptions.
