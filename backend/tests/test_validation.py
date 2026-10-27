from app.services.validation_service import validate_mandatory_fields, MANDATORY_FIELDS


def test_missing_mandatory_field():
    """Verify that omitting a mandatory field generates a high-severity finding."""
    # Provide all mandatory fields EXCEPT institution_name
    fields = [
        {"field_name": "application_id", "field_value": "APP-12345"},
        {"field_name": "address", "field_value": "123 Education Boulevard, New Delhi"},
        {"field_name": "director_name", "field_value": "Dr. A. Sharma"},
        {"field_name": "phone", "field_value": "9876543210"},
        {"field_name": "email", "field_value": "info@institute.edu"},
        {"field_name": "affiliation", "field_value": "State Technical Board"}
    ]

    findings = validate_mandatory_fields(fields, document_id="doc-1", filename="application_form.pdf")

    assert len(findings) == 1
    missing = findings[0]
    assert missing["finding_type"] == "missing_field"
    assert missing["severity"] == "high"
    assert missing["field_name"] == "institution_name"
    assert "Missing field: institution_name" in missing["title"]


def test_all_fields_present():
    """Verify that when all mandatory fields are present, zero missing-field findings are generated."""
    fields = [
        {"field_name": f, "field_value": f"sample_val_{f}"}
        for f in MANDATORY_FIELDS
    ]

    findings = validate_mandatory_fields(fields, document_id="doc-2", filename="complete_doc.pdf")
    assert len(findings) == 0


def test_multiple_missing():
    """Verify that omitting multiple mandatory fields produces corresponding findings for each."""
    # Omit both 'email' and 'phone'
    fields = [
        {"field_name": "institution_name", "field_value": "Delhi Engineering Academy"},
        {"field_name": "application_id", "field_value": "APP-9988"},
        {"field_name": "address", "field_value": "Sector 14 Institutional Zone"},
        {"field_name": "director_name", "field_value": "Prof. R. Varma"},
        {"field_name": "affiliation", "field_value": "Central Technical University"}
    ]

    findings = validate_mandatory_fields(fields, document_id="doc-3", filename="partially_filled.pdf")

    assert len(findings) == 2
    missing_names = {f["field_name"] for f in findings}
    assert missing_names == {"phone", "email"}
    assert all(f["severity"] == "high" for f in findings)
