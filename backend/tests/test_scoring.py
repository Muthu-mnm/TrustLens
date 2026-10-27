from app.services.scoring_service import calculate_risk_score, SEVERITY_WEIGHTS


def test_score_no_findings():
    """Verify that an application with zero findings receives a 100 trust score and Low risk band."""
    result = calculate_risk_score([])
    assert result["score"] == 100.0
    assert result["band"] == "Low"
    assert result["breakdown"]["critical"] == 0
    assert result["breakdown"]["high"] == 0


def test_score_high_findings():
    """Verify that 5 high findings reduce the score significantly."""
    findings = [{"severity": "high"} for _ in range(5)]
    result = calculate_risk_score(findings)

    expected_deduction = 5 * SEVERITY_WEIGHTS["high"]  # 5 * 15 = 75
    expected_score = 100.0 - expected_deduction        # 25.0

    assert result["score"] == expected_score
    assert result["score"] < 50.0
    assert result["band"] == "High"


def test_score_critical_findings():
    """Verify that 3 critical findings place the application in the Critical risk band."""
    findings = [{"severity": "critical"} for _ in range(3)]
    result = calculate_risk_score(findings)

    expected_deduction = 3 * SEVERITY_WEIGHTS["critical"]  # 3 * 30 = 90
    expected_score = 100.0 - expected_deduction           # 10.0

    assert result["score"] == expected_score
    assert result["band"] == "Critical"
    assert result["breakdown"]["critical"] == 3


def test_score_breakdown_keys():
    """Verify that score breakdown dictionary contains all 5 severity keys."""
    result = calculate_risk_score([])
    required_keys = {"critical", "high", "medium", "low", "info"}
    assert required_keys.issubset(set(result["breakdown"].keys()))
