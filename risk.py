"""
Risk interpretation layer.

Converts structured scan data into
a scored operational risk classification.
"""

from rules import build_interpretation_result

HIGH_RISK_THRESHOLD = 9
MEDIUM_RISK_THRESHOLD = 5


def _build_risk_summary(level, connectivity, findings):
    """
    Create a consultant-style summary sentence for the report header.
    """

    if not connectivity.get("reachable"):
        return (
            "The website could not be reached during the request. "
            "Configuration analysis could not be completed."
        )

    if not findings:
        return (
            "The website is reachable and serving content. Only minor "
            "configuration improvements or informational observations were identified."
        )

    if level == "High":
        return (
            "A significant operational issue was observed that may affect "
            "availability, trust, or maintenance reliability."
        )

    if level == "Medium":
        return (
            "The site is reachable and serving content, but several "
            "configuration improvements are recommended."
        )

    return (
        "The website is reachable and serving content. Only minor "
        "configuration improvements or informational observations were identified."
    )


def _issue_message_from_finding(finding):
    """
    Convert a finding into the flatter issue wording used by the current report.
    """

    if finding.get("recommendation"):
        return f"{finding['observation']} {finding['recommendation']}"

    return finding["observation"]


def _determine_override(findings):
    """
    Apply explicit high-risk overrides for severe operational conditions.
    """

    override_mapping = {
        "finding.connectivity.unreachable": "Site unreachable",
        "finding.tls.invalid": "TLS invalid",
        "finding.tls.expiring_soon": "TLS expiry under 30 days",
        "finding.connectivity.server_error": "Server error response",
    }

    finding_ids = {finding["id"] for finding in findings}
    for finding_id, override in override_mapping.items():
        if finding_id in finding_ids:
            return override

    return None


def analyze_risk(scan_result):
    """
    Evaluate structured findings and compute overall risk level.
    """

    connectivity = scan_result["connectivity"]
    interpretation_result = build_interpretation_result(scan_result)
    scan_result["evidence"] = interpretation_result["evidence"]
    scan_result["observations"] = interpretation_result["observations"]
    scan_result["findings"] = interpretation_result["findings"]
    scan_result["recommendations"] = interpretation_result["recommendations"]

    findings = scan_result["findings"]
    score = sum(finding["score"] for finding in findings)
    override = _determine_override(findings)

    if override:
        level = "High"
    elif score >= HIGH_RISK_THRESHOLD:
        level = "High"
    elif score >= MEDIUM_RISK_THRESHOLD:
        level = "Medium"
    else:
        level = "Low"

    contributors = [
        finding["id"] for finding in findings if finding["score"] > 0
    ]
    issues = [
        {
            "id": finding["id"],
            "severity": finding["risk_contribution"],
            "score": finding["score"],
            "message": _issue_message_from_finding(finding),
        }
        for finding in findings
    ]

    return {
        "level": level,
        "score": score,
        "summary": _build_risk_summary(level, connectivity, findings),
        "contributors": contributors,
        "issues": issues,
        "override": override,
    }
