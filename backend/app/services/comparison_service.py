import uuid
from datetime import datetime

COMPARABLE_FIELDS: list[str] = [
    "institution_name",
    "application_id",
    "address",
    "director_name",
    "phone",
    "email"
]


def normalize_value(val: str) -> str:
    """Normalize string value for robust cross-document comparison."""
    if not val:
        return ""
    # Strip spaces, lower case, replace multiple spaces with single space
    import re
    cleaned = re.sub(r"\s+", " ", val.strip().lower())
    # Remove surrounding punctuation
    return cleaned.strip(".,;:\"'")


def compare_documents(
    all_doc_fields: list[dict],
    application_id: str = ""
) -> list[dict]:
    """
    Compare field values across multiple documents within an application.
    
    all_doc_fields: list of dicts:
        [
            {
                "document_id": str,
                "filename": str,
                "fields": [
                    {"field_name": str, "field_value": str}
                ]
            }
        ]

    Returns:
        list of Finding dicts with finding_type="mismatch" and severity="high"
    """
    if not all_doc_fields or len(all_doc_fields) < 2:
        return []

    findings: list[dict] = []
    seen_mismatches: set[tuple[str, str, str]] = set()

    # Compare pairwise across documents
    for i in range(len(all_doc_fields)):
        doc1 = all_doc_fields[i]
        doc1_id = doc1.get("document_id", "")
        doc1_name = doc1.get("filename", "Doc 1")
        doc1_field_map = {
            f.get("field_name"): f.get("field_value")
            for f in doc1.get("fields", [])
            if f.get("field_name") and f.get("field_value")
        }

        for j in range(i + 1, len(all_doc_fields)):
            doc2 = all_doc_fields[j]
            doc2_id = doc2.get("document_id", "")
            doc2_name = doc2.get("filename", "Doc 2")
            doc2_field_map = {
                f.get("field_name"): f.get("field_value")
                for f in doc2.get("fields", [])
                if f.get("field_name") and f.get("field_value")
            }

            for field_name in COMPARABLE_FIELDS:
                val1 = doc1_field_map.get(field_name)
                val2 = doc2_field_map.get(field_name)

                if val1 and val2:
                    norm1 = normalize_value(val1)
                    norm2 = normalize_value(val2)

                    if norm1 != norm2:
                        pair_key = (field_name, min(doc1_name, doc2_name), max(doc1_name, doc2_name))
                        if pair_key not in seen_mismatches:
                            seen_mismatches.add(pair_key)
                            findings.append({
                                "id": str(uuid.uuid4()),
                                "application_id": application_id,
                                "document_id": doc1_id or None,
                                "finding_type": "mismatch",
                                "severity": "high",
                                "title": f"Field Mismatch: {field_name}",
                                "description": (
                                    f"Inconsistent values detected for mandatory field '{field_name}' "
                                    f"between '{doc1_name}' and '{doc2_name}'."
                                ),
                                "evidence": f"'{doc1_name}': '{val1}' vs '{doc2_name}': '{val2}'",
                                "rule_id": "COMPARE-001",
                                "rule_version": "1.0",
                                "field_name": field_name,
                                "page_number": 0,
                                "review_status": "pending",
                                "review_comment": None,
                                "reviewed_by": None,
                                "reviewed_at": None,
                                "created_at": datetime.utcnow()
                            })

    return findings
