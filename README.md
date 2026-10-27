# TrustLens – Explainable AI Decision-Support for AICTE Application Scrutiny

> **SIH Problem Statement**: SIH26261 – V-Matrix  
> **Team**: 5 Members | Smart India Hackathon (SIH) 2024  
> **Status**: MVP / Prototype  

---

> [!CAUTION]
> **PROTOTYPE – NOT AN OFFICIAL AICTE SYSTEM**  
> TrustLens is an independent prototype developed exclusively for the Smart India Hackathon (SIH 2024). It is **not** endorsed by, officially affiliated with, or deployed by the All India Council for Technical Education (AICTE). All institutional records, documents, names, and numbers used for demonstrations are synthetic test artifacts generated for evaluation purposes only.

---

## 📌 Executive Summary

Every year, AICTE evaluates thousands of technical education applications for approvals, intake expansions, and new institutions. Scrutiny officers manually review dozens of uploaded documents—ranging from affiliation certificates and land title deeds to faculty registers and infrastructure floor plans. 

**TrustLens** is an explainable AI decision-support web application engineered to accelerate document scrutiny while keeping the human officer firmly in control. It features:
- Automated OCR and regex-based structured field extraction.
- Cross-document comparison flagging discrepancies across multiple files in the same dossier.
- Duplicate document detection using SHA-256 (exact matches) and perceptual hashing (pHash).
- Forensic image inspection heuristics including Error-Level Analysis (ELA).
- A transparent, weighted compliance rule engine producing an advisory risk score.
- Fine-grained human officer review controls, tamper-evident audit logging, and automated executive PDF report export.

---

## 🏛 Architecture Overview

```
                                      +--------------------------------------------+
                                      |         Scrutiny Officer Browser           |
                                      +--------------------------------------------+
                                                            |
                                                            v
                                      +--------------------------------------------+
                                      |          React 18 + Vite Frontend          |
                                      |     (Tailwind CSS, Lucide Icons, Tabs)     |
                                      +--------------------------------------------+
                                                            |
                                                     HTTP REST APIs
                                                            |
                                                            v
+-------------------------------------------------------------------------------------------------------------------+
|                                            FastAPI Backend Server (:8000)                                         |
+-------------------------------------------------------------------------------------------------------------------+
|  [Routers]                                                                                                        |
|  * /api/health            * /api/applications         * /api/applications/{id}/documents                          |
|  * /api/analyze           * /api/findings             * /api/findings/{id}/review         * /api/report           |
+-------------------------------------------------------------------------------------------------------------------+
|  [Core Services]                                                                                                  |
|  +-----------------------+  +-----------------------+  +-----------------------+  +----------------------------+  |
|  |     OCR Service       |  |   Extraction Service  |  |   Duplicate Service   |  |        ELA Service         |  |
|  |  (PyMuPDF+Tesseract)  |  | (Regex Entity Parser) |  |   (SHA-256 + pHash)   |  | (Compression Forensics)   |  |
|  +-----------------------+  +-----------------------+  +-----------------------+  +----------------------------+  |
|  +--------------------------------------------------+  +-------------------------------------------------------+  |
|  |             Compliance Rule Engine               |  |              Advisory Risk Scoring Engine             |  |
|  |      (Configurable rules via rules.json)         |  |          (Transparent weighted factor model)          |  |
|  +--------------------------------------------------+  +-------------------------------------------------------+  |
|  +--------------------------------------------------+  +-------------------------------------------------------+  |
|  |            Audit Trail Engine                    |  |               ReportLab PDF Generator                 |  |
|  |     (Hash-chained cryptographic event log)       |  |          (Executive Scrutiny Dossier PDF)             |  |
|  +--------------------------------------------------+  +-------------------------------------------------------+  |
+-------------------------------------------------------------------------------------------------------------------+
                                    |                                       |
                                    v                                       v
                     +----------------------------+          +-----------------------------+
                     |    SQLite Database (.db)   |          |  Local Upload Storage       |
                     |  (Applications, Findings)  |          |  (backend/uploads/)         |
                     +----------------------------+          +-----------------------------+
```

---

## 💻 Prerequisites

Ensure your host environment meets these requirements prior to setup:

| Dependency | Minimum Version | Notes |
|---|---|---|
| **Python** | 3.10+ | Required for backend and test data generator |
| **Node.js** | 18+ (LTS recommended) | Required for frontend Vite build |
| **Tesseract OCR** | 5.x | Required for OCR image text extraction |
| **Git** | 2.x | Version control |

### Installing Tesseract OCR

#### Windows
1. **Option A (Chocolatey)**:
   ```powershell
   choco install tesseract
   ```
2. **Option B (Direct Installer)**:
   - Download the installer from the official UB-Mannheim repository:  
     [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
   - Install to the default directory: `C:\Program Files\Tesseract-OCR`
   - Add `C:\Program Files\Tesseract-OCR` to your system `PATH` environment variable.

#### macOS
```bash
brew install tesseract
```

#### Ubuntu / Debian Linux
```bash
sudo apt update
sudo apt install -y tesseract-ocr libtesseract-dev
```

---

## 🚀 Installation & Running

### Windows Setup

#### 1. Clone the repository
```bash
git clone <repo> && cd SIH
```

#### 2. Start Backend Server
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 3. Start Frontend Dashboard (in a separate terminal)
```powershell
cd frontend
npm install
npm run dev
```

---

### macOS / Linux Setup

#### 1. Clone the repository
```bash
git clone <repo> && cd SIH
```

#### 2. Start Backend Server
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 3. Start Frontend Dashboard (in a separate terminal)
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Generate Synthetic Test Data

A dedicated script generates 7 synthetic test documents with edge cases (complete application, cross-document name mismatches, missing mandatory fields, identical bitwise duplicates, altered image whiteouts, and low-contrast scans).

```bash
cd test_data
pip install fpdf2 Pillow
python generate_test_docs.py
```

Generated files will be saved in `test_data/samples/`:
- `sample_01_complete.pdf`
- `sample_02a_mismatch.pdf`
- `sample_02b_mismatch.pdf`
- `sample_03_missing_fields.pdf`
- `sample_04a_duplicate.png`
- `sample_04b_duplicate.png`
- `sample_05_altered.png`
- `sample_06_low_quality.pdf`

---

## 🔬 Run Automated Backend Tests

The backend includes test coverage validating OCR processing, regex extraction, hash duplicate detection, rule evaluation, and report generation.

```bash
cd backend
pytest tests/ -v
```

---

## 🌐 Access Points & Service URLs

| Interface | URL | Purpose |
|---|---|---|
| **Frontend Web Dashboard** | [http://localhost:5173](http://localhost:5173) | Interactive Scrutiny Officer Workstation |
| **Interactive API Docs (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) | OpenAPI interactive endpoint testing |
| **ReDoc API Documentation** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Alternate clean REST API reference |
| **System Health Endpoint** | [http://localhost:8000/api/health](http://localhost:8000/api/health) | Real-time health & dependency verification |

---

## 📊 Feature Status Matrix

| Feature | Status | Notes |
|---|---|---|
| **Document Upload** | ✅ Implemented | Supports PDF, JPG, PNG, TIFF formats with client/server validation |
| **OCR Text Extraction** | ✅ Implemented | Dual-engine approach using PyMuPDF (digital text) + Tesseract OCR (scans) |
| **Field Extraction** | ✅ Implemented | Robust regex-based parser extracting 10+ standard AICTE application fields |
| **Mandatory Field Validation** | ✅ Implemented | Configurable checklist checking for missing essential institutional metadata |
| **Cross-Document Comparison** | ✅ Implemented | Detects discrepancies (e.g. Institution Name) across multiple files in a dossier |
| **Exact Duplicate Detection** | ✅ Implemented | SHA-256 cryptographic hash matching against application and global index |
| **Perceptual Duplicate Detection** | ✅ Implemented | Perceptual hashing (imagehash pHash) detects resized/re-encoded document duplicates |
| **Error-Level Analysis (ELA)** | ✅ Implemented | Heuristic compression variance highlighting edited patches (advisory only) |
| **Compliance Rule Engine** | ✅ Implemented | Deterministic, transparent rule engine driven by customizable `rules.json` |
| **Advisory Risk Scoring** | ✅ Implemented | Transparent 0–100 weighted scoring with severity breakdown and explanation |
| **Officer Review Controls** | ✅ Implemented | Accept, reject, or override any finding with required audit commentary |
| **PDF Report Generation** | ✅ Implemented | Produces executive multi-page Scrutiny Dossier PDF using ReportLab |
| **Audit Trail** | ✅ Implemented | Simplified cryptographic hash-chained event log recording every action |
| **DigiLocker Integration** | 🔮 Future Work | Production integration requires authorized API credentials & gateway access |
| **API Setu Integration** | 🔮 Future Work | National Academic Depository & land registry verification via API Setu |
| **Trained CNN Forgery Detection** | 🔮 Future Work | Deep learning patch-forgery model requires domain dataset & benchmark |
| **LayoutLMv3 Document Understanding** | 🔮 Future Work | Multimodal transformer for semi-structured tabular and stamp spatial extraction |
| **YOLO Floor-Plan Compliance** | 🔮 Future Work | Computer vision model to measure room areas on uploaded architectural blueprints |
| **PostgreSQL Migration** | 🔮 Future Work | Production migration from SQLite to PostgreSQL with connection pooling |
| **Docker Deployment** | 🔮 Future Work | Multi-container docker-compose setup for orchestrating backend, frontend, DB |

---

## 🛠 Troubleshooting Guide

### 1. Tesseract OCR Not Found (`pytesseract.TesseractNotFoundError`)
- **Symptom**: Backend logs show `tesseract is not installed or it's not in your PATH`.
- **Solution (Windows)**:
  1. Confirm Tesseract is installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`.
  2. Add `C:\Program Files\Tesseract-OCR` to your System Environment Variable `PATH` and restart your terminal.
  3. Alternatively, specify the path in your `.env` file:
     ```env
     TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
     ```
- **Solution (macOS/Linux)**: Verify binary presence with `which tesseract`. If missing, reinstall using `brew install tesseract` or `sudo apt install tesseract-ocr`.

### 2. Port Already in Use (Port 8000 or 5173)
- **Symptom**: `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)`
- **Solution (Windows PowerShell)**:
  ```powershell
  # Find process occupying port 8000
  netstat -ano | findstr :8000
  # Terminate PID (replace <PID>)
  taskkill /PID <PID> /F
  ```
- **Solution (macOS/Linux)**:
  ```bash
  lsof -ti:8000 | xargs kill -9
  ```

### 3. Cross-Origin Resource Sharing (CORS) Errors
- **Symptom**: Browser console indicates: `Access to fetch at ... has been blocked by CORS policy`.
- **Solution**: Ensure your frontend URL (`http://localhost:5173`) is listed in the `origins` array inside `backend/app/main.py`. By default, TrustLens allows `["http://localhost:5173", "http://127.0.0.1:5173"]`.

### 4. `imagehash` or `scipy` Install Failures
- **Symptom**: `ModuleNotFoundError: No module named 'imagehash'` or compiler errors during `scipy` build.
- **Solution**: Upgrade pip and ensure pre-compiled binary wheels are pulled:
  ```bash
  python -m pip install --upgrade pip setuptools wheel
  pip install imagehash scipy
  ```

### 5. PyMuPDF (`fitz`) Issues on Windows
- **Symptom**: Build errors when compiling PyMuPDF from source.
- **Solution**: Install the pre-built PyMuPDF wheel directly:
  ```powershell
  pip install --only-binary :all: PyMuPDF==1.24.1
  ```

### 6. Large File Upload Failures (`413 Payload Too Large`)
- **Symptom**: Uploading large multi-page scans (>25MB) fails with HTTP 413 or timeout.
- **Solution**: TrustLens is preconfigured with a 35MB per-file upload limit. Ensure multi-page scans are optimized or adjust `MAX_UPLOAD_SIZE_MB=50` in `backend/app/config/settings.py`.

---

## 👥 SIH Team Allocation

| Team Member | Functional Ownership | Core Modules |
|---|---|---|
| **Member 1** | Frontend UI & Scrutiny Workstation | `frontend/src/pages/*`, `frontend/src/components/*` |
| **Member 2** | OCR & Field Extraction Pipeline | `backend/app/services/ocr_service.py`, `extraction_service.py` |
| **Member 3** | CV, Duplicates & Tampering Analysis | `backend/app/services/duplicate_service.py`, `ela_service.py` |
| **Member 4** | Compliance Rule Engine & Risk Scoring | `backend/app/services/rule_engine.py`, `scoring_service.py` |
| **Member 5** | Backend Architecture, Reports & Tests | `backend/app/main.py`, `report_service.py`, `tests/*` |

---

## ⚖️ Ethics & Human-in-the-Loop Philosophy

AICTE application scrutiny determines the educational future and legal compliance of technical institutions. TrustLens explicitly adheres to **Explainable, Human-Centric AI**:
1. **Advisory Role Only**: TrustLens never automatically accepts or rejects an application.
2. **Transparent Reasoning**: Every risk score displays its mathematical equation, contributing findings, and source text snippets.
3. **Officer Override**: Scrutiny officers can accept, reject, or annotate any flagged finding.
4. **Accountability**: All actions are logged into a cryptographic hash-chained audit trail to ensure transparency and institutional trust.
