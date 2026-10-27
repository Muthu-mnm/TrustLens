import re
from typing import Any

FIELD_PATTERNS: dict[str, list[str]] = {
    "institution_name": [
        r"(?:institution|college|university|institute)\s*(?:name)?\s*[:\-]\s*([^\n\r]+)",
        r"^([A-Z][A-Za-z0-9\s,\.&'\-]+(?:College|University|Institute|School|Academy)[^\n\r]*)"
    ],
    "application_id": [
        r"(?:application\s*(?:no|id|number))\s*[:\-]\s*([A-Za-z0-9_\-/]+)"
    ],
    "address": [
        r"(?:campus\s*address|postal\s*address|address)\s*[:\-]\s*([^\n\r]+(?:\n[^\n\r]+){0,2})"
    ],
    "director_name": [
        r"(?:director|principal|head\s*of\s*institution)\s*(?:name)?\s*[:\-]\s*([^\n\r]+)"
    ],
    "phone": [
        r"(?:phone|mobile|tel(?:ephone)?)\s*[:\-]\s*([+\d\s\-\(\)]{10,16})",
        r"\b([6-9]\d{9})\b"
    ],
    "email": [
        r"(?:email|e-mail)\s*[:\-]\s*([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",
        r"\b([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b"
    ],
    "established_year": [
        r"(?:established|founded|year\s*of\s*establishment|estd\.?)\s*[:\-]?\s*(\d{4})"
    ],
    "affiliation": [
        r"(?:affiliated\s*to|affiliation)\s*[:\-]\s*([^\n\r]+)"
    ],
    "date": [
        r"(?:date)\s*[:\-]\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})"
    ],
    "state": [
        r"(?:state)\s*[:\-]\s*([^\n\r,]+)"
    ],
    "district": [
        r"(?:district)\s*[:\-]\s*([^\n\r,]+)"
    ],
    "pincode": [
        r"(?:pin\s*code|pincode|postal\s*code)\s*[:\-]?\s*(\b[1-9]\d{5}\b)",
        r"\b([1-9]\d{5})\b"
    ],
    "total_intake": [
        r"(?:total\s*intake|sanctioned\s*intake|approved\s*intake)\s*[:\-]\s*(\d+)"
    ],
    "programs_offered": [
        r"(?:programs?|courses?)\s*(?:offered)?\s*[:\-]\s*([^\n\r]+)"
    ]
}


def clean_extracted_value(value: str) -> str:
    """Clean extra spaces, punctuation and line breaks from extracted values."""
    if not value:
        return ""
    cleaned = value.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    # Remove leading/trailing quotes or punctuation often introduced by OCR
    cleaned = cleaned.strip("\"'-,:; ")
    return cleaned


def extract_fields(pages: list[dict] | str) -> list[dict]:
    """
    Search extracted text across all pages for target AICTE application fields.
    Each page in `pages` should be a dict: {"page": int, "text": str}.
    If a string is passed, it is treated as a single page.
    
    Returns:
        list of dicts: [
            {
                "field_name": str,
                "field_value": str,
                "confidence": float,
                "page_number": int
            }
        ]
    """
    if isinstance(pages, str):
        pages = [{"page": 1, "text": pages}]

    if not pages:
        return []

    extracted: list[dict] = []
    found_fields: set[str] = set()

    for field_name, patterns in FIELD_PATTERNS.items():
        field_found = False
        for pattern_idx, pattern_str in enumerate(patterns):
            if field_found:
                break
            
            # Base confidence: 0.95 for primary pattern, 0.85 for secondary fallbacks
            base_confidence = 0.95 if pattern_idx == 0 else 0.85
            compiled_regex = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)

            for page in pages:
                page_text = page.get("text", "")
                page_num = page.get("page", 1)

                if not page_text:
                    continue

                match = compiled_regex.search(page_text)
                if match:
                    raw_val = match.group(1) if match.groups() else match.group(0)
                    cleaned_val = clean_extracted_value(raw_val)

                    if cleaned_val and field_name not in found_fields:
                        confidence = base_confidence
                        if len(cleaned_val) > 2:
                            confidence = min(0.99, round(confidence, 2))

                        extracted.append({
                            "field_name": field_name,
                            "field_value": cleaned_val,
                            "confidence": confidence,
                            "page_number": page_num
                        })
                        found_fields.add(field_name)
                        field_found = True
                        break

    return extracted
