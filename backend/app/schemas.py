from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------
# Health & Generic Responses
# ---------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    service: str = "TrustLens API"
    dependencies: Optional[dict[str, str]] = None


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


# ---------------------------------------------------------
# Document Schemas
# ---------------------------------------------------------
class DocumentResponse(BaseModel):
    id: str
    application_id: str
    filename: str
    original_filename: Optional[str] = None
    doc_type: str = "general_document"
    file_hash: str
    page_count: int = 0
    file_size: int = 0
    status: str = "uploaded"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# ExtractedField Schemas
# ---------------------------------------------------------
class ExtractedFieldResponse(BaseModel):
    id: str
    document_id: str
    field_name: str
    field_value: str
    confidence: float = 0.0
    page_number: int = 0

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Finding Schemas
# ---------------------------------------------------------
class FindingResponse(BaseModel):
    id: str
    application_id: str
    document_id: Optional[str] = None
    finding_type: str  # missing_field|mismatch|duplicate|compliance|ela_anomaly
    severity: str      # info|low|medium|high|critical
    title: str
    description: str
    evidence: str = ""
    rule_id: Optional[str] = None
    rule_version: Optional[str] = None
    field_name: Optional[str] = None
    page_number: int = 0
    review_status: str = "pending"  # pending|reviewed|dismissed|clarification_needed
    review_comment: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Review Action Schemas
# ---------------------------------------------------------
class ReviewActionRequest(BaseModel):
    finding_id: Optional[str] = None
    review_status: str  # reviewed|dismissed|clarification_needed
    comment: Optional[str] = ""
    reviewed_by: str = "Scrutiny Officer"


class ReviewActionResponse(FindingResponse):
    pass


# ---------------------------------------------------------
# Audit Entry Schemas
# ---------------------------------------------------------
class AuditEntryResponse(BaseModel):
    id: str
    application_id: str
    action: str
    actor: str
    details: str
    previous_hash: Optional[str] = None
    entry_hash: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditVerificationResponse(BaseModel):
    valid: bool
    chain_valid: bool
    total_entries: int
    verified_entries: int = 0
    broken_at_index: Optional[int] = None
    tampered_at_index: Optional[int] = None
    details: str
    message: str


# ---------------------------------------------------------
# Application Schemas
# ---------------------------------------------------------
class ApplicationCreate(BaseModel):
    app_id: str
    app_type: str = "Engineering & Technology"
    institution_name: str


class ApplicationResponse(BaseModel):
    id: str
    app_id: str
    app_type: str
    institution_name: str
    status: str = "uploaded"
    created_at: datetime
    updated_at: Optional[datetime] = None
    document_count: int = 0
    finding_count: int = 0
    risk_score: Optional[float] = 0.0
    risk_band: Optional[str] = "Low"
    trust_score: Optional[float] = 100.0

    model_config = ConfigDict(from_attributes=True)


class ApplicationDetailResponse(ApplicationResponse):
    documents: list[DocumentResponse] = []


class ApplicationListResponse(BaseModel):
    applications: list[ApplicationResponse] = []
    total: int = 0

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Analysis Result Schemas
# ---------------------------------------------------------
class AnalysisResultResponse(BaseModel):
    application_id: str
    status: str
    extracted_fields: list[ExtractedFieldResponse] = []
    findings: list[FindingResponse] = []
    risk_score: float = 0.0
    risk_band: str = "Low"
    trust_score: Optional[float] = 100.0
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    score_explanation: Optional[str] = None
    analyzed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
