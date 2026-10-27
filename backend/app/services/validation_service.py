import uuid
from datetime import datetime

MANDATORY_FIELDS: list[str] = [
    "institution_name",
    "application_id",
    "address",
    "director_name",
    "phone",
    "email",
    "affiliation"
]


def validate_mandatory_fields(
    extracted_fields: list[dict],
    document_id: str = "",
    filename: str = "document",
    application_id: str = ""
) -> list[dict]:
    """
    Validate that all mandatory AICTE application fields are present in the extracted fields.
    For each missing mandatory field, generates a Finding dict with severity 'high'.
    """
    present_field_names = {
        f.get("field_name")
        for f in extracted_fields
        if f.get("field_name") and str(f.get("field_value", "")).strip()
    }

    findings: list[dict] = []

    for field in MANDATORY_FIELDS:
        if field not in present_field_names:
            findings.append({
                "id": str(uuid.uuid4()),
                "application_id": application_id,
                "document_id": document_id or None,
                "finding_type": "missing_field",
                "severity": "high",
                "title": f"Missing field: {field}",
                "description": f"Mandatory compliance field '{field}' was not identified in document '{filename}'.",
                "evidence": f"Document '{filename}' was scanned for required field '{field}'. No valid value was extracted.",
                "rule_id": "MANDATORY-001",
                "rule_version": "1.0",
                "field_name": field,
                "page_number": 0,
                "review_status": "pending",
                "review_comment": None,
                "reviewed_by": None,
                "reviewed_at": None,
                "created_at": datetime.utcnow()
            })

    return findings
