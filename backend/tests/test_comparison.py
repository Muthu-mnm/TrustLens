from app.services.comparison_service import compare_documents


def test_name_mismatch():
    """Verify that inconsistent institution names across two documents trigger a mismatch finding."""
    all_doc_fields = [
        {
            "document_id": "doc-uuid-1",
            "filename": "aicte_application_form.pdf",
            "fields": [
                {"field_name": "institution_name", "field_value": "ABC College of Engineering"},
                {"field_name": "application_id", "field_value": "APP-001"}
            ]
        },
        {
            "document_id": "doc-uuid-2",
            "filename": "land_ownership_deed.pdf",
            "fields": [
                {"field_name": "institution_name", "field_value": "XYZ Polytechnic Institute"},
                {"field_name": "application_id", "field_value": "APP-001"}
            ]
        }
    ]

    findings = compare_documents(all_doc_fields, application_id="app-1")

    assert len(findings) >= 1
    mismatch = [f for f in findings if f["field_name"] == "institution_name"][0]
    assert mismatch["finding_type"] == "mismatch"
    assert mismatch["severity"] == "high"
    assert "Field Mismatch: institution_name" in mismatch["title"]
    assert "ABC College of Engineering" in mismatch["evidence"]
    assert "XYZ Polytechnic Institute" in mismatch["evidence"]


def test_no_mismatch():
    """Verify that consistent field values across documents produce zero mismatch findings."""
    all_doc_fields = [
        {
            "document_id": "doc-uuid-1",
            "filename": "form_part1.pdf",
            "fields": [
                {"field_name": "institution_name", "field_value": "National Institute of Science"},
                {"field_name": "phone", "field_value": "9876543210"}
            ]
        },
        {
            "document_id": "doc-uuid-2",
            "filename": "form_part2.pdf",
            "fields": [
                {"field_name": "institution_name", "field_value": "national institute of science"},
                {"field_name": "phone", "field_value": "+91 9876543210"}
            ]
        }
    ]

    findings = compare_documents(all_doc_fields, application_id="app-1")
    name_mismatches = [f for f in findings if f["field_name"] == "institution_name"]
    assert len(name_mismatches) == 0


def test_single_document():
    """Verify that with only a single document, cross-document comparison returns no findings."""
    all_doc_fields = [
        {
            "document_id": "doc-uuid-1",
            "filename": "sole_document.pdf",
            "fields": [
                {"field_name": "institution_name", "field_value": "Apex Engineering College"}
            ]
        }
    ]

    findings = compare_documents(all_doc_fields, application_id="app-1")
    assert findings == []
