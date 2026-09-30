"""
Rule evaluation entry points for evidence, observations, findings, and recommendations.
"""

from .common import sort_evidence, sort_findings, sort_observations, sort_recommendations
from .cookies import evaluate_cookie_rules
from .core import (
    evaluate_cache_rules,
    evaluate_compression_rules,
    evaluate_connectivity_rules,
    evaluate_platform_rules,
    evaluate_tls_rules,
)
from .headers import evaluate_header_rules


def _empty_result():
    """
    Create the root interpretation container.
    """

    return {
        "evidence": [],
        "observations": [],
        "findings": [],
        "recommendations": [],
    }


def _dedupe_by_id(items):
    """
    Preserve first-seen items while removing duplicate identifiers.
    """

    deduped_items = []
    seen_ids = set()

    for item in items:
        item_id = item["id"]
        if item_id in seen_ids:
            continue

        seen_ids.add(item_id)
        deduped_items.append(item)

    return deduped_items


def build_interpretation_result(scan_result):
    """
    Generate the structured Phase 5 interpretation artifacts.
    """

    result = _empty_result()

    connectivity_result = evaluate_connectivity_rules(scan_result)
    result["evidence"].extend(connectivity_result["evidence"])
    result["observations"].extend(connectivity_result["observations"])
    result["findings"].extend(connectivity_result["findings"])
    result["recommendations"].extend(connectivity_result["recommendations"])

    if not scan_result["connectivity"].get("reachable"):
        result["evidence"] = sort_evidence(_dedupe_by_id(result["evidence"]))
        result["observations"] = sort_observations(_dedupe_by_id(result["observations"]))
        result["findings"] = sort_findings(_dedupe_by_id(result["findings"]))
        result["recommendations"] = sort_recommendations(
            _dedupe_by_id(result["recommendations"])
        )
        return result

    for evaluator in (
        evaluate_tls_rules,
        evaluate_header_rules,
        evaluate_cookie_rules,
        evaluate_cache_rules,
        evaluate_compression_rules,
        evaluate_platform_rules,
    ):
        evaluator_result = evaluator(scan_result)
        result["evidence"].extend(evaluator_result["evidence"])
        result["observations"].extend(evaluator_result["observations"])
        result["findings"].extend(evaluator_result["findings"])
        result["recommendations"].extend(evaluator_result["recommendations"])

    result["evidence"] = sort_evidence(_dedupe_by_id(result["evidence"]))
    result["observations"] = sort_observations(_dedupe_by_id(result["observations"]))
    result["findings"] = sort_findings(_dedupe_by_id(result["findings"]))
    result["recommendations"] = sort_recommendations(
        _dedupe_by_id(result["recommendations"])
    )
    return result
