from typing import Any

SEVERITY_WEIGHTS: dict[str, int] = {
    "critical": 30,
    "high": 15,
    "medium": 8,
    "low": 3,
    "info": 0
}

BASE_SCORE: int = 100


def calculate_risk_score(findings: list[dict | Any]) -> dict:
    """
    Calculate application compliance trust score and risk classification.
    Deducts points for each finding according to its severity.
    Score is capped between 0.0 and 100.0.

    Risk Bands (based on risk penalty incurred):
        0 - 25   : Low
        26 - 50  : Medium
        51 - 75  : High
        76 - 100 : Critical

    Returns:
        dict: {
            "score": float,
            "band": str,
            "breakdown": {"critical": int, "high": int, "medium": int, "low": int, "info": int},
            "explanation": str
        }
    """
    breakdown: dict[str, int] = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0
    }

    total_deductions = 0

    for item in findings:
        if isinstance(item, dict):
            sev = item.get("severity", "medium")
        else:
            sev = getattr(item, "severity", "medium")

        sev_clean = str(sev).lower().strip() if sev else "medium"
        if sev_clean not in breakdown:
            sev_clean = "medium"

        breakdown[sev_clean] += 1
        total_deductions += SEVERITY_WEIGHTS.get(sev_clean, 0)

    # Score deducts from base score 100 down to minimum 0.0
    score = max(0.0, float(BASE_SCORE - total_deductions))

    # Risk points represent the accumulated penalty
    risk_points = min(100, total_deductions)

    if risk_points <= 25:
        band = "Low"
    elif risk_points <= 50:
        band = "Medium"
    elif risk_points <= 75:
        band = "High"
    else:
        band = "Critical"

    explanation = (
        f"Compliance Trust Score: {score:.1f}/100. "
        f"Total penalty: {risk_points} points based on {len(findings)} detected findings. "
        f"Assigned Risk Band: {band}."
    )

    return {
        "score": round(score, 1),
        "band": band,
        "breakdown": breakdown,
        "explanation": explanation
    }
