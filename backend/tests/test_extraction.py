from app.services.extraction_service import extract_fields


def test_extract_institution_name():
    """Verify that institution name is accurately extracted from formatted text."""
    sample_text = (
        "AICTE Verification Form\n"
        "Institution Name: ABC College of Engineering\n"
        "Affiliated to State University"
    )
    extracted = extract_fields([{"page": 1, "text": sample_text}])
    field_dict = {f["field_name"]: f["field_value"] for f in extracted}

    assert "institution_name" in field_dict
    assert "ABC College of Engineering" in field_dict["institution_name"]


def test_extract_email():
    """Verify official email address is detected and extracted."""
    sample_text = "For official communication, write to contact.registrar@abccollege.edu.in regarding scrutiny."
    extracted = extract_fields([{"page": 1, "text": sample_text}])
    field_dict = {f["field_name"]: f["field_value"] for f in extracted}

    assert "email" in field_dict
    assert field_dict["email"] == "contact.registrar@abccollege.edu.in"


def test_extract_phone():
    """Verify contact phone number is detected and extracted."""
    sample_text = "Principal Office Tel: +91-9876543210. Available 9am to 5pm."
    extracted = extract_fields([{"page": 1, "text": sample_text}])
    field_dict = {f["field_name"]: f["field_value"] for f in extracted}

    assert "phone" in field_dict
    assert "9876543210" in field_dict["phone"]


def test_extract_no_fields():
    """Verify empty text or text with no matching patterns returns empty list."""
    empty_res = extract_fields([{"page": 1, "text": ""}])
    assert empty_res == []

    random_noise = extract_fields([{"page": 1, "text": "lorem ipsum dolor sit amet consectetur adipiscing elit"}])
    assert len(random_noise) == 0
