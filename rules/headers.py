"""
Header evidence and finding generation.
"""

from knowledge_base import HEADER_KNOWLEDGE_BASE

from .common import (
    build_evidence,
    build_finding,
    build_observation,
    build_recommendation,
    normalize_id_token,
    risk_score,
)

HEADER_SUBJECT_IDS = {
    "content-security-policy": "csp",
    "strict-transport-security": "hsts",
    "x-content-type-options": "x_content_type_options",
    "x-frame-options": "x_frame_options",
    "referrer-policy": "referrer_policy",
    "permissions-policy": "permissions_policy",
}


def _empty_result():
    return {
        "evidence": [],
        "observations": [],
        "findings": [],
        "recommendations": [],
    }


def _header_subject(normalized_name):
    """
    Produce a stable header subject token for IDs.
    """

    return HEADER_SUBJECT_IDS.get(normalized_name, normalize_id_token(normalized_name))


def _header_evidence_id(normalized_name):
    """
    Produce the evidence identifier for a header.
    """

    return f"header.{normalize_id_token(normalized_name)}"


def _matches_recommended_value(observed_value, recommended_values):
    """
    Check whether an observed header value matches a known recommended value.
    """

    if observed_value is None:
        return False

    normalized_observed = observed_value.strip().lower()
    return any(
        normalized_observed == recommended_value.strip().lower()
        for recommended_value in recommended_values
    )


def _unexpected_value_recommendation(header_name, recommended_values):
    """
    Generate restrained advice for a known header value mismatch.
    """

    if not recommended_values:
        return "Review whether the observed header value is intentional."

    if len(recommended_values) == 1:
        return (
            f"Review the {header_name} header value and consider using "
            f"{recommended_values[0]}."
        )

    joined_values = " or ".join(recommended_values)
    return (
        f"Review the {header_name} header value and consider using "
        f"{joined_values}."
    )


def _iter_header_entries(headers_result):
    """
    Iterate through categorized header entries in stable category order.
    """

    for category_entries in headers_result["categorized"].values():
        for entry in category_entries:
            yield entry


def evaluate_header_rules(scan_result):
    """
    Generate deterministic header evidence and findings.
    """

    result = _empty_result()
    headers_result = scan_result["headers"]

    for entry in _iter_header_entries(headers_result):
        evidence_id = _header_evidence_id(entry["normalized_name"])
        metadata = HEADER_KNOWLEDGE_BASE.get(entry["normalized_name"])

        result["evidence"].append(
            build_evidence(
                evidence_id,
                entry["category"],
                "HTTP response header",
                entry["name"],
                entry["value"],
                entry["present"],
                entry["value"],
            )
        )

        if not entry["known"]:
            continue

        subject = _header_subject(entry["normalized_name"])

        if not entry["present"] and entry["expected"] == "present":
            risk_contribution = entry["risk_contribution"]
            score = risk_score(risk_contribution)

            if score == 0:
                continue

            observation_id = f"observation.header.{subject}.missing"
            finding_id = f"finding.header.{subject}.missing"
            observation_message = f"The response does not include the {entry['name']} header."

            result["observations"].append(
                build_observation(
                    observation_id,
                    evidence_id,
                    entry["category"],
                    observation_message,
                )
            )
            result["findings"].append(
                build_finding(
                    finding_id,
                    entry["category"],
                    f"{entry['name']} header not observed",
                    [evidence_id],
                    observation_message,
                    entry["interpretation"],
                    entry["recommendation"],
                    risk_contribution,
                    score,
                )
            )

            if entry["recommendation"]:
                result["recommendations"].append(
                    build_recommendation(
                        f"recommendation.header.{subject}.review",
                        finding_id,
                        risk_contribution,
                        entry["recommendation"],
                    )
                )

        if (
            entry["present"]
            and metadata
            and metadata["recommended_values"]
            and not _matches_recommended_value(
                entry["value"],
                metadata["recommended_values"],
            )
        ):
            observation_id = f"observation.header.{subject}.unexpected_value"
            finding_id = f"finding.header.{subject}.unexpected_value"
            observation_message = (
                f"The response includes the {entry['name']} header with "
                f"value: {entry['value']}."
            )
            recommendation_message = _unexpected_value_recommendation(
                entry["name"],
                metadata["recommended_values"],
            )

            result["observations"].append(
                build_observation(
                    observation_id,
                    evidence_id,
                    entry["category"],
                    observation_message,
                )
            )
            result["findings"].append(
                build_finding(
                    finding_id,
                    entry["category"],
                    f"{entry['name']} header value should be reviewed",
                    [evidence_id],
                    observation_message,
                    (
                        "The observed value does not match the recommended "
                        "values tracked by Site Inspector."
                    ),
                    recommendation_message,
                    "Low",
                    risk_score("Low"),
                )
            )
            result["recommendations"].append(
                build_recommendation(
                    f"recommendation.header.{subject}.review_value",
                    finding_id,
                    "Low",
                    recommendation_message,
                )
            )

        if entry["present"] and metadata and metadata["deprecated"]:
            risk_contribution = metadata["risk_if_present"]
            score = metadata["score_if_present"]
            observation_id = f"observation.header.{subject}.present"
            finding_id = f"finding.header.{subject}.deprecated_present"
            observation_message = f"The response includes the {entry['name']} header."

            result["observations"].append(
                build_observation(
                    observation_id,
                    evidence_id,
                    entry["category"],
                    observation_message,
                )
            )
            result["findings"].append(
                build_finding(
                    finding_id,
                    entry["category"],
                    f"{entry['name']} header observed",
                    [evidence_id],
                    observation_message,
                    entry["interpretation"],
                    entry["recommendation"],
                    risk_contribution,
                    score,
                )
            )

            if entry["recommendation"]:
                result["recommendations"].append(
                    build_recommendation(
                        f"recommendation.header.{subject}.review_legacy_use",
                        finding_id,
                        risk_contribution,
                        entry["recommendation"],
                    )
                )

    return result
