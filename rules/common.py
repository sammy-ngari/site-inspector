"""
Shared builders and ordering helpers for deterministic rule evaluation.
"""

import re

RISK_SCORES = {
    "Informational": 0,
    "Low": 1,
    "Medium": 2,
    "High": 3,
}

RISK_SORT_ORDER = {
    "High": 0,
    "Medium": 1,
    "Low": 2,
    "Informational": 3,
}

CATEGORY_SORT_ORDER = {
    "Connectivity": 0,
    "TLS": 1,
    "Security & Browser Protection": 2,
    "Cookies & Sessions": 3,
    "Caching & Freshness": 4,
    "Compression & Transfer": 5,
    "Performance": 6,
    "Server / Application Disclosure": 7,
    "CDN / Proxy / Edge Infrastructure": 8,
    "Platform": 9,
    "HTML": 10,
    "Other": 11,
}


def risk_score(risk_contribution):
    """
    Convert a textual risk contribution into its deterministic numeric score.
    """

    return RISK_SCORES.get(risk_contribution, 0)


def normalize_id_token(value):
    """
    Convert free-form text into a stable identifier token.
    """

    normalized_value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return normalized_value or "item"


def build_evidence(evidence_id, category, source, name, value, present, raw):
    """
    Build a schema-aligned evidence object.
    """

    return {
        "id": evidence_id,
        "category": category,
        "source": source,
        "name": name,
        "value": value,
        "present": present,
        "raw": raw,
    }


def build_observation(observation_id, evidence_id, category, message):
    """
    Build a schema-aligned observation object.
    """

    return {
        "id": observation_id,
        "evidence_id": evidence_id,
        "category": category,
        "message": message,
    }


def build_finding(
    finding_id,
    category,
    title,
    evidence_ids,
    observation,
    interpretation,
    recommendation,
    risk_contribution,
    score,
):
    """
    Build a schema-aligned finding object.
    """

    return {
        "id": finding_id,
        "category": category,
        "title": title,
        "evidence_ids": evidence_ids,
        "observation": observation,
        "interpretation": interpretation,
        "recommendation": recommendation,
        "risk_contribution": risk_contribution,
        "score": score,
    }


def build_recommendation(recommendation_id, finding_id, priority, message):
    """
    Build a schema-aligned recommendation object.
    """

    return {
        "id": recommendation_id,
        "finding_id": finding_id,
        "priority": priority,
        "message": message,
    }


def sort_evidence(evidence):
    """
    Keep evidence ordering deterministic for reports and future JSON output.
    """

    return sorted(
        evidence,
        key=lambda item: (
            CATEGORY_SORT_ORDER.get(item["category"], 99),
            item["name"].lower(),
            item["id"],
        ),
    )


def sort_observations(observations):
    """
    Keep observations ordering deterministic.
    """

    return sorted(
        observations,
        key=lambda item: (
            CATEGORY_SORT_ORDER.get(item["category"], 99),
            item["id"],
        ),
    )


def sort_findings(findings):
    """
    Keep findings ordered by severity and then category.
    """

    return sorted(
        findings,
        key=lambda item: (
            RISK_SORT_ORDER.get(item["risk_contribution"], 99),
            CATEGORY_SORT_ORDER.get(item["category"], 99),
            item["title"].lower(),
            item["id"],
        ),
    )


def sort_recommendations(recommendations):
    """
    Keep recommendations ordered by priority and identifier.
    """

    return sorted(
        recommendations,
        key=lambda item: (
            RISK_SORT_ORDER.get(item["priority"], 99),
            item["id"],
        ),
    )
