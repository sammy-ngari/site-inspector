"""
Current-check rule evaluation outside the header and cookie domains.
"""

from .common import (
    build_evidence,
    build_finding,
    build_observation,
    build_recommendation,
    risk_score,
)

SLOW_RESPONSE_THRESHOLD_SECONDS = 2.0
VERY_SLOW_RESPONSE_THRESHOLD_SECONDS = 5.0
TLS_EXPIRING_SOON_DAYS = 30
TLS_EXPIRING_REVIEW_DAYS = 60


def _empty_result():
    return {
        "evidence": [],
        "observations": [],
        "findings": [],
        "recommendations": [],
    }


def evaluate_connectivity_rules(scan_result):
    """
    Generate findings from connectivity and response timing evidence.
    """

    result = _empty_result()
    connectivity = scan_result["connectivity"]
    target = scan_result["target"]

    reachable = connectivity.get("reachable")
    status_code = connectivity.get("status_code")
    response_time = connectivity.get("response_time_seconds")
    redirect_count = connectivity.get("redirect_count", 0)
    final_url = target.get("final_url")

    result["evidence"].append(
        build_evidence(
            "connectivity.reachable",
            "Connectivity",
            "HTTP request",
            "Reachability",
            reachable,
            reachable,
            reachable,
        )
    )
    result["evidence"].append(
        build_evidence(
            "connectivity.status_code",
            "Connectivity",
            "HTTP response",
            "Status code",
            status_code,
            status_code is not None,
            status_code,
        )
    )
    result["evidence"].append(
        build_evidence(
            "connectivity.redirect_count",
            "Connectivity",
            "HTTP response",
            "Redirect count",
            redirect_count,
            True,
            redirect_count,
        )
    )
    result["evidence"].append(
        build_evidence(
            "connectivity.final_url",
            "Connectivity",
            "HTTP response",
            "Final URL",
            final_url,
            final_url is not None,
            final_url,
        )
    )
    result["evidence"].append(
        build_evidence(
            "performance.response_time_seconds",
            "Performance",
            "HTTP response",
            "Response time",
            response_time,
            response_time is not None,
            response_time,
        )
    )

    if not reachable:
        finding_id = "finding.connectivity.unreachable"
        observation_message = "The website could not be reached during the request."
        recommendation_message = (
            "Confirm DNS, hosting availability, firewall rules, and server health."
        )

        result["observations"].append(
            build_observation(
                "observation.connectivity.unreachable",
                "connectivity.reachable",
                "Connectivity",
                observation_message,
            )
        )
        result["findings"].append(
            build_finding(
                finding_id,
                "Connectivity",
                "Website unreachable",
                ["connectivity.reachable"],
                observation_message,
                "The site did not return a usable HTTP response during the inspection.",
                recommendation_message,
                "High",
                risk_score("High"),
            )
        )
        result["recommendations"].append(
            build_recommendation(
                "recommendation.connectivity.review_availability",
                finding_id,
                "High",
                recommendation_message,
            )
        )
        return result

    if status_code is not None and status_code >= 500:
        finding_id = "finding.connectivity.server_error"
        observation_message = f"The homepage returned an HTTP {status_code} server error."
        recommendation_message = (
            "Review server logs, application health, and upstream dependencies."
        )

        result["observations"].append(
            build_observation(
                "observation.connectivity.server_error",
                "connectivity.status_code",
                "Connectivity",
                observation_message,
            )
        )
        result["findings"].append(
            build_finding(
                finding_id,
                "Connectivity",
                "Server error response observed",
                ["connectivity.status_code"],
                observation_message,
                "The inspected homepage returned a server-side error response.",
                recommendation_message,
                "High",
                risk_score("High"),
            )
        )
        result["recommendations"].append(
            build_recommendation(
                "recommendation.connectivity.review_server_health",
                finding_id,
                "High",
                recommendation_message,
            )
        )
    elif status_code is not None and 400 <= status_code < 500:
        finding_id = "finding.connectivity.client_error"
        observation_message = f"The homepage returned an HTTP {status_code} client error."
        recommendation_message = (
            "Confirm whether the homepage is intended to return this status code."
        )

        result["observations"].append(
            build_observation(
                "observation.connectivity.client_error",
                "connectivity.status_code",
                "Connectivity",
                observation_message,
            )
        )
        result["findings"].append(
            build_finding(
                finding_id,
                "Connectivity",
                "Client error response observed",
                ["connectivity.status_code"],
                observation_message,
                "The inspected homepage returned a client-facing error response.",
                recommendation_message,
                "Medium",
                risk_score("Medium"),
            )
        )
        result["recommendations"].append(
            build_recommendation(
                "recommendation.connectivity.confirm_homepage_status",
                finding_id,
                "Medium",
                recommendation_message,
            )
        )

    if final_url and final_url.startswith("http://"):
        finding_id = "finding.connectivity.http_final_url"
        observation_message = "The final inspected response remained on HTTP."
        recommendation_message = (
            "Review whether HTTPS delivery should be preferred for the final response."
        )

        result["observations"].append(
            build_observation(
                "observation.connectivity.http_final_url",
                "connectivity.final_url",
                "Connectivity",
                observation_message,
            )
        )
        result["findings"].append(
            build_finding(
                finding_id,
                "Connectivity",
                "Final response remained on HTTP",
                ["connectivity.final_url"],
                observation_message,
                "HTTPS delivery was not observed for the final page response.",
                recommendation_message,
                "Low",
                risk_score("Low"),
            )
        )
        result["recommendations"].append(
            build_recommendation(
                "recommendation.connectivity.review_https_delivery",
                finding_id,
                "Low",
                recommendation_message,
            )
        )

    if redirect_count > 5:
        finding_id = "finding.connectivity.excessive_redirects"
        observation_message = (
            f"The inspected page completed after {redirect_count} redirects."
        )
        recommendation_message = (
            "Review canonical URL, HTTPS enforcement, and www/non-www redirect configuration."
        )

        result["observations"].append(
            build_observation(
                "observation.connectivity.excessive_redirects",
                "connectivity.redirect_count",
                "Connectivity",
                observation_message,
            )
        )
        result["findings"].append(
            build_finding(
                finding_id,
                "Connectivity",
                "Excessive redirects observed",
                ["connectivity.redirect_count"],
                observation_message,
                "The homepage required a long redirect chain before the final response.",
                recommendation_message,
                "Medium",
                risk_score("Medium"),
            )
        )
        result["recommendations"].append(
            build_recommendation(
                "recommendation.connectivity.review_redirect_chain",
                finding_id,
                "Medium",
                recommendation_message,
            )
        )
    elif redirect_count >= 3:
        finding_id = "finding.connectivity.redirect_review"
        observation_message = (
            f"The inspected page completed after {redirect_count} redirects."
        )
        recommendation_message = (
            "Review redirect chain to reduce unnecessary hops where practical."
        )

        result["observations"].append(
            build_observation(
                "observation.connectivity.redirect_review",
                "connectivity.redirect_count",
                "Connectivity",
                observation_message,
            )
        )
        result["findings"].append(
            build_finding(
                finding_id,
                "Connectivity",
                "Multiple redirects observed",
                ["connectivity.redirect_count"],
                observation_message,
                "The homepage required multiple redirects before the final response.",
                recommendation_message,
                "Low",
                risk_score("Low"),
            )
        )
        result["recommendations"].append(
            build_recommendation(
                "recommendation.connectivity.review_redirect_hops",
                finding_id,
                "Low",
                recommendation_message,
            )
        )

    if response_time is not None and response_time > VERY_SLOW_RESPONSE_THRESHOLD_SECONDS:
        finding_id = "finding.performance.very_slow_response"
        observation_message = "The response took more than five seconds to complete."
        recommendation_message = (
            "Review server health, backend latency, caching, and hosting resource constraints."
        )

        result["observations"].append(
            build_observation(
                "observation.performance.very_slow_response",
                "performance.response_time_seconds",
                "Performance",
                observation_message,
            )
        )
        result["findings"].append(
            build_finding(
                finding_id,
                "Performance",
                "Very slow homepage response observed",
                ["performance.response_time_seconds"],
                observation_message,
                "Very slow initial response may affect usability and reliability for visitors.",
                recommendation_message,
                "High",
                risk_score("High"),
            )
        )
        result["recommendations"].append(
            build_recommendation(
                "recommendation.performance.review_response_latency",
                finding_id,
                "High",
                recommendation_message,
            )
        )
    elif response_time is not None and response_time > SLOW_RESPONSE_THRESHOLD_SECONDS:
        finding_id = "finding.performance.slow_response"
        observation_message = "The response took more than two seconds to complete."
        recommendation_message = (
            "Review hosting performance, backend processing time, caching, and CDN behaviour."
        )

        result["observations"].append(
            build_observation(
                "observation.performance.slow_response",
                "performance.response_time_seconds",
                "Performance",
                observation_message,
            )
        )
        result["findings"].append(
            build_finding(
                finding_id,
                "Performance",
                "Slow homepage response observed",
                ["performance.response_time_seconds"],
                observation_message,
                "Slow initial response may affect user experience, especially on slower networks.",
                recommendation_message,
                "Medium",
                risk_score("Medium"),
            )
        )
        result["recommendations"].append(
            build_recommendation(
                "recommendation.performance.review_response_time",
                finding_id,
                "Medium",
                recommendation_message,
            )
        )

    return result


def evaluate_tls_rules(scan_result):
    """
    Generate findings from TLS validity and expiry evidence.
    """

    result = _empty_result()
    tls = scan_result["tls"]

    result["evidence"].append(
        build_evidence(
            "tls.valid",
            "TLS",
            "TLS certificate inspection",
            "TLS validity",
            tls.get("valid"),
            tls.get("valid"),
            tls.get("error") or tls.get("valid"),
        )
    )
    result["evidence"].append(
        build_evidence(
            "tls.days_until_expiry",
            "TLS",
            "TLS certificate inspection",
            "Days until certificate expiry",
            tls.get("days_until_expiry"),
            tls.get("days_until_expiry") is not None,
            tls.get("days_until_expiry"),
        )
    )

    if tls.get("checked") and not tls.get("valid"):
        finding_id = "finding.tls.invalid"
        observation_message = "A valid TLS certificate was not confirmed."
        recommendation_message = (
            "Review certificate installation, hostname coverage, certificate chain, and expiry status."
        )

        result["observations"].append(
            build_observation(
                "observation.tls.invalid",
                "tls.valid",
                "TLS",
                observation_message,
            )
        )
        result["findings"].append(
            build_finding(
                finding_id,
                "TLS",
                "TLS certificate validation failed",
                ["tls.valid"],
                observation_message,
                "TLS validation did not complete successfully for the inspected hostname.",
                recommendation_message,
                "High",
                risk_score("High"),
            )
        )
        result["recommendations"].append(
            build_recommendation(
                "recommendation.tls.review_validity",
                finding_id,
                "High",
                recommendation_message,
            )
        )
        return result

    days_until_expiry = tls.get("days_until_expiry")
    if not tls.get("valid") or days_until_expiry is None:
        return result

    if days_until_expiry < TLS_EXPIRING_SOON_DAYS:
        finding_id = "finding.tls.expiring_soon"
        observation_message = (
            f"The TLS certificate expires in {days_until_expiry} days."
        )
        recommendation_message = "Renew or replace the TLS certificate before expiry."

        result["observations"].append(
            build_observation(
                "observation.tls.expiring_soon",
                "tls.days_until_expiry",
                "TLS",
                observation_message,
            )
        )
        result["findings"].append(
            build_finding(
                finding_id,
                "TLS",
                "TLS certificate expiry is approaching soon",
                ["tls.days_until_expiry"],
                observation_message,
                "Certificate expiry is close enough to deserve prompt renewal review.",
                recommendation_message,
                "High",
                risk_score("High"),
            )
        )
        result["recommendations"].append(
            build_recommendation(
                "recommendation.tls.renew_certificate",
                finding_id,
                "High",
                recommendation_message,
            )
        )
    elif days_until_expiry < TLS_EXPIRING_REVIEW_DAYS:
        finding_id = "finding.tls.expiring_review"
        observation_message = (
            f"The TLS certificate expires in {days_until_expiry} days."
        )
        recommendation_message = (
            "Schedule certificate renewal to avoid service disruption."
        )

        result["observations"].append(
            build_observation(
                "observation.tls.expiring_review",
                "tls.days_until_expiry",
                "TLS",
                observation_message,
            )
        )
        result["findings"].append(
            build_finding(
                finding_id,
                "TLS",
                "TLS certificate renewal window is approaching",
                ["tls.days_until_expiry"],
                observation_message,
                "Certificate renewal planning should begin soon to avoid avoidable expiry pressure.",
                recommendation_message,
                "Medium",
                risk_score("Medium"),
            )
        )
        result["recommendations"].append(
            build_recommendation(
                "recommendation.tls.schedule_renewal",
                finding_id,
                "Medium",
                recommendation_message,
            )
        )

    return result


def evaluate_cache_rules(scan_result):
    """
    Generate findings from cache configuration evidence.
    """

    result = _empty_result()
    cache = scan_result["cache"]

    for field_name, display_name in (
        ("cache_control", "Cache-Control"),
        ("expires", "Expires"),
        ("etag", "ETag"),
        ("last_modified", "Last-Modified"),
    ):
        value = cache.get(field_name)
        result["evidence"].append(
            build_evidence(
                f"cache.{field_name}",
                "Caching & Freshness",
                "HTTP response header",
                display_name,
                value,
                value is not None,
                value,
            )
        )

    if cache.get("configured"):
        return result

    finding_id = "finding.cache.configuration_absent"
    observation_message = "No cache configuration headers were observed in the response."
    recommendation_message = (
        "Consider defining cache behaviour appropriate to the content type and freshness requirements."
    )

    result["observations"].append(
        build_observation(
            "observation.cache.configuration_absent",
            "cache.cache_control",
            "Caching & Freshness",
            observation_message,
        )
    )
    result["findings"].append(
        build_finding(
            finding_id,
            "Caching & Freshness",
            "Cache configuration not observed",
            [
                "cache.cache_control",
                "cache.expires",
                "cache.etag",
                "cache.last_modified",
            ],
            observation_message,
            "The response does not currently expose cache behaviour guidance for browsers or intermediaries.",
            recommendation_message,
            "Low",
            risk_score("Low"),
        )
    )
    result["recommendations"].append(
        build_recommendation(
            "recommendation.cache.define_behaviour",
            finding_id,
            "Low",
            recommendation_message,
        )
    )

    return result


def _is_compressible_content_type(content_type):
    """
    Determine whether the observed content type is text-like and typically compressible.
    """

    if not content_type:
        return False

    normalized_content_type = content_type.lower()
    if normalized_content_type.startswith("text/"):
        return True

    return any(
        token in normalized_content_type
        for token in ("html", "json", "javascript", "css", "xml")
    )


def evaluate_compression_rules(scan_result):
    """
    Generate findings from compression evidence.
    """

    result = _empty_result()
    compression = scan_result["compression"]
    content_type = scan_result["response"].get("content_type")

    result["evidence"].append(
        build_evidence(
            "compression.content_encoding",
            "Compression & Transfer",
            "HTTP response header",
            "Content-Encoding",
            compression.get("content_encoding"),
            compression.get("content_encoding") is not None,
            compression.get("content_encoding"),
        )
    )

    if compression.get("enabled") or not _is_compressible_content_type(content_type):
        return result

    finding_id = "finding.compression.not_observed"
    observation_message = "Compression was not observed for a text-based response."
    recommendation_message = (
        "For compressible text-based content, consider enabling Brotli or gzip compression."
    )

    result["observations"].append(
        build_observation(
            "observation.compression.not_observed",
            "compression.content_encoding",
            "Compression & Transfer",
            observation_message,
        )
    )
    result["findings"].append(
        build_finding(
            finding_id,
            "Compression & Transfer",
            "Compression not observed for text-based content",
            ["compression.content_encoding"],
            observation_message,
            "The returned content appears compressible, but HTTP compression was not observed.",
            recommendation_message,
            "Low",
            risk_score("Low"),
        )
    )
    result["recommendations"].append(
        build_recommendation(
            "recommendation.compression.enable_text_compression",
            finding_id,
            "Low",
            recommendation_message,
        )
    )

    return result


def evaluate_platform_rules(scan_result):
    """
    Generate informational platform findings from observed CMS indicators.
    """

    result = _empty_result()
    platform = scan_result["platform"]

    result["evidence"].append(
        build_evidence(
            "platform.cms_detection",
            "Platform",
            "HTML response body",
            "CMS detection",
            platform.get("name"),
            platform.get("detected"),
            platform.get("evidence"),
        )
    )

    if not platform.get("detected"):
        return result

    if platform.get("name") == "WordPress":
        finding_id = "finding.platform.wordpress_detected"
        observation_message = "The returned HTML includes markers consistent with WordPress."
        recommendation_message = (
            "WordPress indicators were observed. Keep core, themes, and plugins maintained."
        )
        title = "WordPress indicators observed"
        interpretation = (
            "WordPress indicators were observed from the single inspected response."
        )
    else:
        platform_name = platform.get("name")
        finding_id = "finding.platform.cms_detected"
        observation_message = (
            f"The returned HTML includes markers consistent with {platform_name}."
        )
        recommendation_message = (
            "Keep the detected platform, themes, plugins, and integrations maintained."
        )
        title = "Platform indicators observed"
        interpretation = (
            "Platform indicators were observed from the single inspected response."
        )

    result["observations"].append(
        build_observation(
            f"observation.{finding_id.split('.', 1)[1]}",
            "platform.cms_detection",
            "Platform",
            observation_message,
        )
    )
    result["findings"].append(
        build_finding(
            finding_id,
            "Platform",
            title,
            ["platform.cms_detection"],
            observation_message,
            interpretation,
            recommendation_message,
            "Informational",
            risk_score("Informational"),
        )
    )
    result["recommendations"].append(
        build_recommendation(
            f"recommendation.{finding_id.split('.', 1)[1]}.maintain",
            finding_id,
            "Informational",
            recommendation_message,
        )
    )

    return result
