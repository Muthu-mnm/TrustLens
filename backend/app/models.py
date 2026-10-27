import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    app_id = Column(String(100), unique=True, index=True, nullable=False)
    app_type = Column(String(100), nullable=False, default="Engineering & Technology")
    institution_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="uploaded")  # uploaded|analyzing|analyzed|reviewed
    risk_score = Column(Float, nullable=True, default=0.0)
    risk_band = Column(String(50), nullable=True, default="Low")  # Low|Medium|High|Critical
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="application", cascade="all, delete-orphan")
    audit_entries = relationship("AuditEntry", back_populates="application", cascade="all, delete-orphan")

    @property
    def document_count(self) -> int:
        return len(self.documents) if self.documents else 0

    @property
    def finding_count(self) -> int:
        return len(self.findings) if self.findings else 0


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    doc_type = Column(String(100), nullable=False, default="general_document")
    file_hash = Column(String(64), nullable=False, index=True)
    page_count = Column(Integer, default=0, nullable=False)
    file_size = Column(Integer, default=0, nullable=False)
    mime_type = Column(String(100), default="application/pdf", nullable=False)
    status = Column(String(50), default="uploaded", nullable=False)  # uploaded|processing|processed|error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    application = relationship("Application", back_populates="documents")
    extracted_fields = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="document")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    field_value = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    page_number = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="extracted_fields")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    finding_type = Column(String(50), nullable=False)  # missing_field|mismatch|duplicate|compliance|ela_anomaly
    severity = Column(String(50), nullable=False)  # info|low|medium|high|critical
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(Text, default="", nullable=False)
    rule_id = Column(String(100), nullable=True)
    rule_version = Column(String(50), nullable=True)
    field_name = Column(String(100), nullable=True)
    page_number = Column(Integer, default=0, nullable=False)
    review_status = Column(String(50), default="pending", nullable=False)  # pending|reviewed|dismissed|clarification_needed
    review_comment = Column(Text, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    application = relationship("Application", back_populates="findings")
    document = relationship("Document", back_populates="findings")


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    actor = Column(String(100), nullable=False)
    details = Column(Text, nullable=False)
    previous_hash = Column(String(64), nullable=True)
    entry_hash = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    application = relationship("Application", back_populates="audit_entries")
