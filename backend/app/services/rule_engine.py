import os
import json
import re
import uuid
import logging
from typing import Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Resolve path to rules.json
CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))
RULES_FILE = os.path.join(CONFIG_DIR, "rules.json")


def load_rules() -> list[dict]:
    """Load configurable compliance rules from JSON file."""
    if not os.path.exists(RULES_FILE):
        logger.warning(f"Rules configuration file not found at {RULES_FILE}")
        return []
    try:
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("rules", [])
    except Exception as e:
        logger.error(f"Failed to load rules from {RULES_FILE}: {e}")
        return []


def _extract_number(val: Any) -> float | None:
    if val is None:
        return None
    cleaned = re.sub(r"[^\d.]", "", str(val))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def evaluate_rules(extracted_fields: list[dict], application: dict) -> list[dict]:
    """
    Evaluate compliance rules against extracted fields and application metadata.
    Returns:
        list of Finding dicts with rule_id, rule_version populated.
    """
    rules = load_rules()
    if not rules:
        return []

    # Map extracted fields into a fast lookup dict
    field_map: dict[str, str] = {}
    for item in extracted_fields:
        if isinstance(item, dict):
            name = item.get("field_name")
            val = item.get("field_value")
        else:
            name = getattr(item, "field_name", None)
            val = getattr(item, "field_value", None)

        if name and val and str(val).strip():
            field_map[name] = str(val).strip()

    # Populate fallback metadata from application if available
    app_id = application.get("id") or application.get("app_id") or ""
    if "institution_name" not in field_map and application.get("institution_name"):
        field_map["institution_name"] = str(application.get("institution_name"))
    if "application_id" not in field_map and application.get("app_id"):
        field_map["application_id"] = str(application.get("app_id"))

    findings: list[dict] = []

    for rule in rules:
        if not rule.get("enabled", True):
            continue

        condition = rule.get("condition", {})
        target_field = condition.get("field", "")
        operator = condition.get("operator", "")
        current_value = field_map.get(target_field, "")

        is_valid = True
        failure_reason = ""

        if operator == "exists":
            if not current_value:
                is_valid = False
                failure_reason = f"Required field '{target_field}' was not found in application documents."

        elif operator == "regex":
            pattern = condition.get("pattern", "")
            if not current_value:
                is_valid = False
                failure_reason = f"Field '{target_field}' is missing to match regex pattern."
            elif not re.search(pattern, current_value):
                is_valid = False
                failure_reason = f"Field '{target_field}' value '{current_value}' does not match pattern '{pattern}'."

        elif operator == "min_length":
            min_len = int(condition.get("value", 0))
            if len(current_value) < min_len:
                is_valid = False
                failure_reason = f"Field '{target_field}' length ({len(current_value)}) is less than required minimum of {min_len} characters."

        elif operator == "greater_than":
            num = _extract_number(current_value)
            target_val = float(condition.get("value", 0))
            if num is None:
                is_valid = False
                failure_reason = f"Field '{target_field}' value '{current_value}' is not a valid number."
            elif not (num > target_val):
                is_valid = False
                failure_reason = f"Field '{target_field}' numerical value ({num}) is not greater than {target_val}."

        elif operator == "numeric_range":
            num = _extract_number(current_value)
            min_val = float(condition.get("min", float("-inf")))
            max_val = float(condition.get("max", float("inf")))
            if num is None:
                is_valid = False
                failure_reason = f"Field '{target_field}' value '{current_value}' is not a valid number for range check."
            elif not (min_val <= num <= max_val):
                is_valid = False
                failure_reason = f"Field '{target_field}' numerical value ({num}) is outside acceptable range [{min_val}, {max_val}]."

        if not is_valid:
            findings.append({
                "id": str(uuid.uuid4()),
                "application_id": app_id,
                "document_id": None,
                "finding_type": "compliance",
                "severity": rule.get("severity", "medium").lower(),
                "title": f"Rule Violation: {rule.get('name')}",
                "description": rule.get("description", ""),
                "evidence": f"{failure_reason} (Rule: {rule.get('id')} v{rule.get('version', '1.0')})",
                "rule_id": rule.get("id"),
                "rule_version": rule.get("version", "1.0"),
                "field_name": target_field,
                "page_number": 0,
                "review_status": "pending",
                "review_comment": None,
                "reviewed_by": None,
                "reviewed_at": None,
                "created_at": datetime.utcnow()
            })

    return findings
