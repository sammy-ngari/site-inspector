"""
Cookie evidence and finding generation.
"""

from .common import (
    build_evidence,
    build_finding,
    build_observation,
    build_recommendation,
    normalize_id_token,
    risk_score,
)

CATEGORY = "Cookies & Sessions"


def _empty_result():
    return {
        "evidence": [],
        "observations": [],
        "findings": [],
        "recommendations": [],
    }


def _cookie_token(cookie_name):
    """
    Convert a cookie name into a stable identifier token.
    """

    return normalize_id_token(cookie_name or "unnamed_cookie")


def evaluate_cookie_rules(scan_result):
    """
    Generate cookie evidence plus attribute-specific findings.
    """

    result = _empty_result()
    cookies_result = scan_result["cookies"]
    final_url = scan_result["target"].get("final_url") or ""

    result["evidence"].append(
        build_evidence(
            "cookie.present",
            CATEGORY,
            "HTTP response header",
            "Set-Cookie headers",
            cookies_result.get("present", False),
            cookies_result.get("present", False),
            None,
        )
    )

    if not cookies_result.get("present"):
        result["observations"].append(
            build_observation(
                "observation.cookie.none_observed",
                "cookie.present",
                CATEGORY,
                "No cookies were observed in the response.",
            )
        )
        return result

    secure_evidence_ids = []
    httponly_evidence_ids = []
    samesite_evidence_ids = []
    domain_evidence_ids = []

    for cookie in cookies_result["cookies"]:
        cookie_token = _cookie_token(cookie.get("name"))
        raw_cookie = cookie.get("raw")

        secure_evidence_id = f"cookie.{cookie_token}.secure"
        result["evidence"].append(
            build_evidence(
                secure_evidence_id,
                CATEGORY,
                "HTTP Set-Cookie header",
                f"{cookie.get('name')} Secure attribute",
                cookie.get("secure"),
                cookie.get("secure"),
                raw_cookie,
            )
        )
        if not cookie.get("secure"):
            secure_evidence_ids.append(secure_evidence_id)

        httponly_evidence_id = f"cookie.{cookie_token}.httponly"
        result["evidence"].append(
            build_evidence(
                httponly_evidence_id,
                CATEGORY,
                "HTTP Set-Cookie header",
                f"{cookie.get('name')} HttpOnly attribute",
                cookie.get("httponly"),
                cookie.get("httponly"),
                raw_cookie,
            )
        )
        if not cookie.get("httponly"):
            httponly_evidence_ids.append(httponly_evidence_id)

        samesite_evidence_id = f"cookie.{cookie_token}.samesite"
        result["evidence"].append(
            build_evidence(
                samesite_evidence_id,
                CATEGORY,
                "HTTP Set-Cookie header",
                f"{cookie.get('name')} SameSite attribute",
                cookie.get("samesite"),
                cookie.get("samesite") is not None,
                raw_cookie,
            )
        )
        if cookie.get("samesite") is None:
            samesite_evidence_ids.append(samesite_evidence_id)

        domain_evidence_id = f"cookie.{cookie_token}.domain"
        result["evidence"].append(
            build_evidence(
                domain_evidence_id,
                CATEGORY,
                "HTTP Set-Cookie header",
                f"{cookie.get('name')} Domain attribute",
                cookie.get("domain"),
                cookie.get("domain") is not None,
                raw_cookie,
            )
        )
        if cookie.get("domain"):
            domain_evidence_ids.append(domain_evidence_id)

    if final_url.startswith("https://") and secure_evidence_ids:
        finding_id = "finding.cookie.secure.missing"
        observation_message = (
            "The response sets one or more cookies without the Secure attribute."
        )
        recommendation_message = (
            "For cookies used over HTTPS, consider adding the Secure "
            "attribute where appropriate."
        )

        result["observations"].append(
            build_observation(
                "observation.cookie.secure.missing",
                secure_evidence_ids[0],
                CATEGORY,
                observation_message,
            )
        )
        result["findings"].append(
            build_finding(
                finding_id,
                CATEGORY,
                "Cookies without Secure attribute observed",
                secure_evidence_ids,
                observation_message,
                (
                    "One or more cookies observed on an HTTPS response are not "
                    "explicitly limited to secure transport."
                ),
                recommendation_message,
                "Medium",
                risk_score("Medium"),
            )
        )
        result["recommendations"].append(
            build_recommendation(
                "recommendation.cookie.secure.add",
                finding_id,
                "Medium",
                recommendation_message,
            )
        )

    if httponly_evidence_ids:
        finding_id = "finding.cookie.httponly.missing"
        observation_message = (
            "The response sets one or more cookies without the HttpOnly attribute."
        )
        recommendation_message = (
            "For session or sensitive cookies, consider adding HttpOnly to "
            "reduce browser script access."
        )

        result["observations"].append(
            build_observation(
                "observation.cookie.httponly.missing",
                httponly_evidence_ids[0],
                CATEGORY,
                observation_message,
            )
        )
        result["findings"].append(
            build_finding(
                finding_id,
                CATEGORY,
                "Cookies without HttpOnly attribute observed",
                httponly_evidence_ids,
                observation_message,
                (
                    "One or more cookies remain accessible to browser scripts, "
                    "which may deserve review if they support session or "
                    "sensitive workflows."
                ),
                recommendation_message,
                "Medium",
                risk_score("Medium"),
            )
        )
        result["recommendations"].append(
            build_recommendation(
                "recommendation.cookie.httponly.add",
                finding_id,
                "Medium",
                recommendation_message,
            )
        )

    if samesite_evidence_ids:
        finding_id = "finding.cookie.samesite.missing"
        observation_message = (
            "The response sets one or more cookies without a SameSite attribute."
        )
        recommendation_message = (
            "Consider setting a SameSite attribute appropriate to the site's "
            "cross-site workflow."
        )

        result["observations"].append(
            build_observation(
                "observation.cookie.samesite.missing",
                samesite_evidence_ids[0],
                CATEGORY,
                observation_message,
            )
        )
        result["findings"].append(
            build_finding(
                finding_id,
                CATEGORY,
                "Cookies without SameSite attribute observed",
                samesite_evidence_ids,
                observation_message,
                (
                    "Cross-site cookie behavior is not explicitly declared for "
                    "one or more observed cookies."
                ),
                recommendation_message,
                "Low",
                risk_score("Low"),
            )
        )
        result["recommendations"].append(
            build_recommendation(
                "recommendation.cookie.samesite.define",
                finding_id,
                "Low",
                recommendation_message,
            )
        )

    if domain_evidence_ids:
        finding_id = "finding.cookie.domain.review"
        observation_message = (
            "The response sets one or more cookies with an explicit Domain attribute."
        )
        recommendation_message = "Review whether the cookie domain scope is intentional."

        result["observations"].append(
            build_observation(
                "observation.cookie.domain.present",
                domain_evidence_ids[0],
                CATEGORY,
                observation_message,
            )
        )
        result["findings"].append(
            build_finding(
                finding_id,
                CATEGORY,
                "Cookies with explicit Domain attribute observed",
                domain_evidence_ids,
                observation_message,
                (
                    "Cookie scope extends beyond the host-only default for one "
                    "or more observed cookies."
                ),
                recommendation_message,
                "Informational",
                risk_score("Informational"),
            )
        )
        result["recommendations"].append(
            build_recommendation(
                "recommendation.cookie.domain.review_scope",
                finding_id,
                "Informational",
                recommendation_message,
            )
        )

    return result
