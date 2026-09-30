"""
Reporting layer.

Formats structured scan data for console output.
"""

import os
import re
import shutil
import sys
import textwrap

ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
FORCE_COLOR = os.environ.get("FORCE_COLOR", "").lower() in {"1", "true", "yes"}
FORCE_STYLE = os.environ.get("SITE_INSPECTOR_FORCE_COLOR", "").lower() in {
    "1",
    "true",
    "yes",
}
STYLE_ENABLED = (
    FORCE_COLOR
    or FORCE_STYLE
    or (
        sys.stdout.isatty()
        and os.environ.get("TERM") != "dumb"
        and "NO_COLOR" not in os.environ
    )
)
REPORT_WIDTH = max(72, min(108, shutil.get_terminal_size((96, 24)).columns))

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

FG_RED = "\033[91m"
FG_GREEN = "\033[92m"
FG_YELLOW = "\033[93m"
FG_BLUE = "\033[94m"
FG_MAGENTA = "\033[95m"
FG_CYAN = "\033[96m"
FG_WHITE = "\033[97m"
FG_GRAY = "\033[90m"


def _style(text, *codes):
    """
    Apply ANSI styling when the terminal supports it.
    """

    if not STYLE_ENABLED or not codes:
        return str(text)

    return f"{''.join(codes)}{text}{RESET}"


def _visible_length(text):
    """
    Calculate visible length without ANSI codes.
    """

    return len(ANSI_ESCAPE_PATTERN.sub("", str(text)))


def _center_text(text):
    """
    Center visible text within the report width.
    """

    padding = max((REPORT_WIDTH - _visible_length(text)) // 2, 0)
    return (" " * padding) + str(text)


def _wrap_text(text, indent=0, hanging=0):
    """
    Wrap plain text to the report width.
    """

    return textwrap.fill(
        str(text),
        width=REPORT_WIDTH,
        initial_indent=" " * indent,
        subsequent_indent=" " * (indent + hanging),
        break_long_words=False,
        break_on_hyphens=False,
    )


def _severity_style(text):
    """
    Style a severity label consistently.
    """

    severity_map = {
        "High": (BOLD, FG_RED),
        "Medium": (BOLD, FG_YELLOW),
        "Low": (BOLD, FG_BLUE),
        "Informational": (BOLD, FG_MAGENTA),
        "Unknown": (BOLD, FG_WHITE),
    }
    return _style(text, *severity_map.get(str(text), (BOLD, FG_WHITE)))


def _status_style(text):
    """
    Style short status values consistently.
    """

    status_map = {
        "Yes": (BOLD, FG_GREEN),
        "No": (BOLD, FG_RED),
        "Observed": (BOLD, FG_GREEN),
        "Missing": (BOLD, FG_YELLOW),
        "Valid": (BOLD, FG_GREEN),
        "Invalid": (BOLD, FG_RED),
        "Not checked": (BOLD, FG_GRAY),
        "Invalid or not verified": (BOLD, FG_RED),
        "Not reached": (BOLD, FG_RED),
    }
    return _style(text, *status_map.get(str(text), (FG_WHITE,)))


def _value_style(text, tone=None):
    """
    Style a value using the requested display tone.
    """

    if tone == "url":
        return _style(text, FG_CYAN, UNDERLINE)
    if tone == "risk":
        return _severity_style(text)
    if tone == "status":
        return _status_style(text)
    if tone == "error":
        return _style(text, BOLD, FG_RED)
    if tone == "note":
        return _style(text, ITALIC, FG_YELLOW)
    if tone == "muted":
        return _style(text, DIM, FG_GRAY)
    if tone == "emphasis":
        return _style(text, BOLD, FG_WHITE)
    if tone == "highlight":
        return _style(text, BOLD, FG_MAGENTA)
    return text


def _print_rule(char="-", color=FG_GRAY):
    """
    Print a full-width rule line.
    """

    print(_style(char * REPORT_WIDTH, DIM, color))


def _print_section_heading(title):
    """
    Render a centered, styled section heading.
    """

    heading = f"===== {title} ====="
    print()
    print(_center_text(_style(heading, BOLD, FG_CYAN)))


def _print_report_title():
    """
    Print the styled report title block.
    """

    title = _style("===== WEBSITE HEALTH REPORT =====", BOLD, FG_MAGENTA)
    subtitle = _style(
        "Structured configuration review from one standard page request.",
        DIM,
        FG_GRAY,
    )

    print()
    print(_center_text(title))
    print(_center_text(subtitle))


def _print_kv(label, value, tone=None, fallback="Not observed"):
    """
    Print a styled key-value line.
    """

    rendered_value = _render_text(value, fallback)
    plain_label = f"{label}:"
    label_text = _style(plain_label, BOLD, FG_CYAN)
    inline_width = REPORT_WIDTH - len(plain_label) - 1

    if inline_width < 20:
        print(label_text)
        wrapped_value = textwrap.wrap(
            rendered_value,
            width=max(REPORT_WIDTH - 2, 20),
            break_long_words=False,
            break_on_hyphens=False,
        )
        for line in wrapped_value or [rendered_value]:
            print(f"  {_value_style(line, tone)}")
        return

    wrapped_value = textwrap.wrap(
        rendered_value,
        width=inline_width,
        break_long_words=False,
        break_on_hyphens=False,
    )
    first_line = wrapped_value[0] if wrapped_value else rendered_value
    print(f"{label_text} {_value_style(first_line, tone)}")

    hanging_indent = " " * (len(plain_label) + 1)
    for line in wrapped_value[1:]:
        print(f"{hanging_indent}{_value_style(line, tone)}")


def _print_wrapped(text, indent=0, hanging=0, tone=None):
    """
    Wrap plain text first, then apply styling to the wrapped result.
    """

    print(_value_style(_wrap_text(text, indent=indent, hanging=hanging), tone))


def _print_block(label, text, tone=None):
    """
    Print a styled label followed by a wrapped paragraph.
    """

    print(_style(f"{label}:", BOLD, FG_MAGENTA))
    _print_wrapped(text, indent=2, tone=tone)


def _print_list_item(text, prefix="-", tone=None, indent=0):
    """
    Print a styled single-line bullet item.
    """

    bullet_text = f"{prefix} {text}"
    _print_wrapped(bullet_text, indent=indent, hanging=len(prefix) + 1, tone=tone)


def _format_bool(value):
    """
    Render a boolean as a consistent Yes/No label.
    """

    return "Yes" if value else "No"


def _render_text(value, fallback="Not observed"):
    """
    Render optional values consistently.
    """

    if value is None or value == "":
        return fallback
    if isinstance(value, bool):
        return _format_bool(value)
    return str(value)


def _format_seconds(value):
    """
    Render response time values consistently.
    """

    if value is None:
        return "Not observed"
    return f"{value} seconds"


def _format_payload_size(size_bytes):
    """
    Render payload size in bytes and KB.
    """

    if size_bytes is None:
        return "Not observed"

    size_kb = round(size_bytes / 1024, 1)
    return f"{size_bytes} bytes ({size_kb} KB)"


def _format_capitalized(value, fallback="Not observed"):
    """
    Render short string values with initial capitalization.
    """

    if value is None or value == "":
        return fallback
    return str(value).capitalize()


def _dedupe_recommendations(recommendations):
    """
    Remove repeated recommendation objects while preserving order.
    """

    deduped_recommendations = []
    seen_ids = set()

    for recommendation in recommendations:
        recommendation_id = recommendation["id"]
        if recommendation_id in seen_ids:
            continue

        seen_ids.add(recommendation_id)
        deduped_recommendations.append(recommendation)

    return deduped_recommendations


def _group_recommendations(recommendations):
    """
    Group recommendations by priority in display order.
    """

    grouped_recommendations = {
        "High": [],
        "Medium": [],
        "Low": [],
        "Informational": [],
    }

    for recommendation in _dedupe_recommendations(recommendations):
        grouped_recommendations.setdefault(recommendation["priority"], []).append(
            recommendation
        )

    return grouped_recommendations


def _build_evidence_lookup(scan_result):
    """
    Build a fast lookup table for structured evidence items.
    """

    return {evidence["id"]: evidence for evidence in scan_result.get("evidence", [])}


def _format_evidence_value(evidence):
    """
    Render an evidence value in a way that matches the console report.
    """

    if not evidence.get("present"):
        if isinstance(evidence.get("value"), bool):
            return _format_bool(evidence["value"])
        return "Not observed"

    value = evidence.get("value")
    if value is None or value == "":
        return "Observed"

    if isinstance(value, bool):
        return _format_bool(value)

    return str(value)


def _top_findings(scan_result, limit=3):
    """
    Return the highest-priority findings for the executive summary.
    """

    return scan_result.get("findings", [])[:limit]


def _recommended_next_action(scan_result):
    """
    Choose the best single next-action sentence for the executive summary.
    """

    recommendations = _dedupe_recommendations(scan_result.get("recommendations", []))
    if recommendations:
        return recommendations[0]["message"]

    if scan_result.get("findings"):
        return (
            "Review the listed configuration findings with the developer, "
            "hosting provider, or system administrator."
        )

    return "No immediate configuration follow-up was generated from the observed response."


def _first_finding(scan_result, category=None, finding_id=None):
    """
    Return the first matching finding for section-specific operational notes.
    """

    for finding in scan_result.get("findings", []):
        if finding_id is not None and finding["id"] == finding_id:
            return finding
        if category is not None and finding["category"] == category:
            return finding

    return None


def _category_heading(title):
    """
    Render a styled category heading inside a section.
    """

    return _style(f"--- {title} ---", BOLD, FG_MAGENTA)


def print_executive_summary(scan_result):
    """
    Print the report's executive summary.
    """

    risk = scan_result["risk"]
    findings = _top_findings(scan_result)

    _print_section_heading("EXECUTIVE SUMMARY")
    _print_kv("Overall Risk Level", risk.get("level", "Unknown"), tone="risk")
    _print_block("Summary", risk.get("summary", "Risk analysis was not available."))
    print(_style("Top Findings:", BOLD, FG_MAGENTA))
    if findings:
        for index, finding in enumerate(findings, start=1):
            severity = _severity_style(finding["risk_contribution"])
            print(f"  {index}. [{severity}] {_style(finding['title'], BOLD, FG_WHITE)}")
    else:
        _print_wrapped(
            "No major findings were generated from the observed response.",
            indent=2,
            tone="muted",
        )
    _print_block(
        "Recommended Next Action",
        _recommended_next_action(scan_result),
        tone="note",
    )
    _print_block(
        "Analysis Scope",
        "This analysis is based solely on publicly exposed configuration observed "
        "during a standard page request.",
        tone="muted",
    )


def print_target_section(scan_result):
    """
    Print the target and request metadata section.
    """

    target = scan_result["target"]
    request = scan_result["request"]

    _print_section_heading("TARGET & REQUEST")
    _print_kv("Input", target.get("input"), tone="emphasis")
    _print_kv("Normalized URL", target.get("normalized_url"), tone="url")
    _print_kv("Hostname", target.get("hostname"), tone="highlight")
    _print_kv("Final URL", target.get("final_url") or "Not reached", tone="url")
    _print_kv("Request Method", request.get("method"), tone="emphasis")
    _print_kv("Timeout", f"{request.get('timeout_seconds')} seconds")
    _print_kv("Redirects Enabled", _format_bool(request.get("redirects_enabled")), tone="status")
    _print_kv(
        "Single Request Model",
        _format_bool(request.get("single_request_model")),
        tone="status",
    )


def print_connectivity_section(scan_result):
    """
    Print connectivity and redirect behavior.
    """

    connectivity = scan_result["connectivity"]

    _print_section_heading("CONNECTIVITY")
    _print_kv("Reachable", _format_bool(connectivity.get("reachable")), tone="status")

    if not connectivity.get("reachable"):
        connectivity_errors = [
            error
            for error in scan_result.get("errors", [])
            if error["component"] == "connectivity"
        ]
        if connectivity_errors:
            _print_block("Error", connectivity_errors[0]["message"], tone="error")
        _print_block(
            "Operational Note",
            "The website could not be reached during the request. "
            "Configuration analysis could not be completed.",
            tone="note",
        )
        return

    status_code = connectivity.get("status_code")
    status_tone = "emphasis"
    if status_code is not None:
        if status_code >= 500:
            status_tone = "error"
        elif status_code >= 400:
            status_tone = "note"
        elif status_code >= 200:
            status_tone = "status"

    _print_kv("Status Code", _render_text(status_code), tone=status_tone)
    _print_kv("Response Time", _format_seconds(connectivity.get("response_time_seconds")))
    _print_kv("Redirect Count", connectivity.get("redirect_count", 0))

    redirect_chain = connectivity.get("redirect_chain", [])
    if redirect_chain:
        print(_style("Redirect Chain:", BOLD, FG_MAGENTA))
        for index, redirect in enumerate(redirect_chain, start=1):
            location = redirect.get("location") or "Not disclosed"
            redirect_text = (
                f"{index}. {redirect.get('status_code')} {redirect.get('url')} -> {location}"
            )
            _print_wrapped(redirect_text, indent=2)


def print_tls_section(scan_result):
    """
    Print TLS certificate evidence.
    """

    tls = scan_result["tls"]

    _print_section_heading("TRANSPORT SECURITY")
    _print_kv("TLS Checked", _format_bool(tls.get("checked")), tone="status")
    certificate_status = "Valid" if tls.get("valid") else "No"
    _print_kv("Certificate Valid", certificate_status, tone="status")
    _print_kv("Days Until Expiry", _render_text(tls.get("days_until_expiry")))
    _print_kv("Not Before", _render_text(tls.get("not_before")))
    _print_kv("Not After", _render_text(tls.get("not_after")))
    _print_kv("Issuer", _render_text(tls.get("issuer"), "Not available"))
    _print_kv("Subject", _render_text(tls.get("subject"), "Not available"))

    if tls.get("error"):
        _print_block("TLS Error", tls["error"], tone="error")

    tls_finding = _first_finding(scan_result, category="TLS")
    if tls_finding and tls_finding.get("recommendation"):
        _print_block("Operational Note", tls_finding["recommendation"], tone="note")


def _render_header_overview(headers_result):
    """
    Print the required header overview summary fields.
    """

    summary = headers_result["summary"]
    _print_kv("Total Observed Headers", summary["total_observed"])
    _print_kv("Known Observed Headers", summary["known_observed"])
    _print_kv("Unknown Observed Headers", summary["unknown_observed"])
    _print_kv("Expected Known Headers Missing", summary["expected_known_missing"])
    _print_kv("Deprecated Headers Observed", summary["deprecated_observed"])
    _print_wrapped(
        "Unknown headers are preserved and shown under Vendor-Specific / Unclassified.",
        tone="muted",
    )


def _render_header_entry(entry):
    """
    Print a single categorized header entry using the v1.2 display shape.
    """

    _print_kv("Header", entry["name"], tone="emphasis")
    if entry["present"] and entry["value"] is not None:
        _print_kv("Value", entry["value"])
    _print_kv(
        "Status",
        "Observed" if entry["present"] else "Missing",
        tone="status",
    )
    _print_kv("Category", entry["category"], tone="highlight")
    _print_block("Interpretation", entry["interpretation"])
    if entry.get("recommendation"):
        _print_block("Recommendation", entry["recommendation"], tone="note")
    _print_kv("Risk Contribution", entry["risk_contribution"], tone="risk")


def _render_header_categories(headers_result):
    """
    Print categorized headers in stable category order.
    """

    any_entries = False

    for category_entries in headers_result["categorized"].values():
        if not category_entries:
            continue

        any_entries = True
        print()
        print(_center_text(_category_heading(category_entries[0]["category"])))
        for index, entry in enumerate(category_entries):
            if index > 0:
                _print_rule()
            _render_header_entry(entry)

    if not any_entries:
        _print_wrapped(
            "No observed or expected headers were available for categorized display.",
            tone="muted",
        )


def print_response_section(scan_result):
    """
    Print final response metadata.
    """

    response = scan_result["response"]

    _print_section_heading("HTTP RESPONSE")
    _print_kv("Status Code", _render_text(response.get("status_code")), tone="status")
    _print_kv("Content-Type", _render_text(response.get("content_type")))
    _print_kv("Content-Length", _render_text(response.get("content_length"), "Not declared"))
    _print_kv("Payload Size", _format_payload_size(response.get("size_bytes")))
    _print_kv("Content-Encoding", _render_text(response.get("encoding")))
    _print_kv("Body Present", _format_bool(response.get("body_present")), tone="status")


def print_header_overview(scan_result):
    """
    Print the header overview section.
    """

    _print_section_heading("HEADER OVERVIEW")
    _render_header_overview(scan_result["headers"])


def print_header_categories(scan_result):
    """
    Print the categorized header sections.
    """

    _print_section_heading("HEADER CATEGORIES")
    _render_header_categories(scan_result["headers"])


def print_cookie_section(scan_result):
    """
    Print cookie summary and per-cookie details.
    """

    cookies = scan_result["cookies"]
    summary = cookies.get("summary", {})

    _print_section_heading("COOKIES & SESSIONS")
    _print_kv("Cookies Present", _format_bool(cookies.get("present")), tone="status")

    if not cookies.get("present"):
        _print_block(
            "Operational Note",
            "No Set-Cookie header was observed in the primary response. "
            "This is not automatically a problem.",
            tone="muted",
        )
        return

    _print_kv("Total Cookies", summary.get("total", 0))
    _print_kv("Cookies with Secure", summary.get("secure_count", 0))
    _print_kv("Cookies with HttpOnly", summary.get("httponly_count", 0))
    _print_kv("Cookies with SameSite", summary.get("samesite_count", 0))
    _print_kv("Missing Secure Count", summary.get("missing_secure_count", 0))
    _print_kv("Missing HttpOnly Count", summary.get("missing_httponly_count", 0))
    _print_kv("Missing SameSite Count", summary.get("missing_samesite_count", 0))
    print(_style("Cookie Details:", BOLD, FG_MAGENTA))
    for index, cookie in enumerate(cookies.get("cookies", []), start=1):
        print(_style(f"  {index}. {cookie['name']}", BOLD, FG_WHITE))
        _print_kv("Secure", "Present" if cookie["secure"] else "Missing", tone="status")
        _print_kv(
            "HttpOnly",
            "Present" if cookie["httponly"] else "Missing",
            tone="status",
        )
        _print_kv("SameSite", _render_text(cookie.get("samesite"), "Missing"))
        _print_kv("Path", _render_text(cookie.get("path")))
        _print_kv("Domain", _render_text(cookie.get("domain")))
        _print_kv("Expires", _render_text(cookie.get("expires")))
        _print_kv("Max-Age", _render_text(cookie.get("max_age")))
        if index < len(cookies.get("cookies", [])):
            _print_rule()


def print_cache_section(scan_result):
    """
    Print cache and freshness indicators.
    """

    cache = scan_result["cache"]
    directives = cache.get("directives", {})
    parsed_directives = []

    if directives.get("max_age") is not None:
        parsed_directives.append(f"max-age={directives['max_age']}")
    for directive_name in (
        "no_cache",
        "no_store",
        "public",
        "private",
        "must_revalidate",
    ):
        if directives.get(directive_name):
            parsed_directives.append(directive_name.replace("_", "-"))

    _print_section_heading("CACHE & FRESHNESS")
    _print_kv("Cache-Control", _render_text(cache.get("cache_control")))
    _print_kv("Expires", _render_text(cache.get("expires")))
    _print_kv("ETag", _render_text(cache.get("etag")))
    _print_kv("Last-Modified", _render_text(cache.get("last_modified")))
    _print_kv("Vary", _render_text(cache.get("vary")))
    _print_kv(
        "Cache Configuration Observed",
        _format_bool(cache.get("configured")),
        tone="status",
    )
    _print_kv(
        "Parsed Directives",
        ", ".join(parsed_directives) if parsed_directives else "None parsed",
    )


def print_compression_section(scan_result):
    """
    Print compression and transfer metadata.
    """

    compression = scan_result["compression"]
    headers = scan_result["headers"]["normalized"]
    transfer_encoding = headers.get("transfer-encoding", {}).get("value")
    accept_ranges = headers.get("accept-ranges", {}).get("value")
    compression_finding = _first_finding(
        scan_result,
        finding_id="finding.compression.not_observed",
    )

    _print_section_heading("COMPRESSION & TRANSFER")
    _print_kv(
        "Compression Enabled",
        _format_bool(compression.get("enabled")),
        tone="status",
    )
    _print_kv("Compression Method", _render_text(compression.get("method")))
    _print_kv("Content-Encoding", _render_text(compression.get("content_encoding")))
    _print_kv("Transfer-Encoding", _render_text(transfer_encoding))
    _print_kv(
        "Content-Length",
        _render_text(scan_result["response"].get("content_length"), "Not declared"),
    )
    _print_kv("Accept-Ranges", _render_text(accept_ranges))

    if compression_finding and compression_finding.get("recommendation"):
        _print_block("Operational Note", compression_finding["recommendation"], tone="note")


def _print_indicator_group(title, indicators):
    """
    Print a grouped list of infrastructure indicators.
    """

    print(_style(f"{title}:", BOLD, FG_MAGENTA))
    if not indicators:
        _print_wrapped("None observed", indent=2, tone="muted")
        return

    for indicator in indicators:
        indicator_text = (
            f"{indicator['provider']}: {indicator['evidence']} "
            f"(confidence: {indicator['confidence']})"
        )
        _print_wrapped(f"- {indicator_text}", indent=2)


def print_infrastructure_section(scan_result):
    """
    Print infrastructure and delivery hints.
    """

    infrastructure = scan_result["infrastructure"]

    _print_section_heading("INFRASTRUCTURE INDICATORS")
    _print_kv("Server", _render_text(infrastructure.get("server"), "Not disclosed"))
    _print_kv(
        "X-Powered-By",
        _render_text(infrastructure.get("x_powered_by"), "Not disclosed"),
    )
    _print_kv("Via", _render_text(infrastructure.get("via")))
    _print_kv("HTTP/3 Hint", _format_bool(infrastructure.get("http3_hint")), tone="status")
    _print_indicator_group("CDN Indicators", infrastructure.get("cdn_indicators", []))
    _print_indicator_group("Proxy Indicators", infrastructure.get("proxy_indicators", []))
    _print_indicator_group("Edge Indicators", infrastructure.get("edge_indicators", []))
    print(_style("Raw Headers Used:", BOLD, FG_MAGENTA))
    raw_headers_used = infrastructure.get("raw_headers_used", [])
    if not raw_headers_used:
        _print_wrapped("None observed", indent=2, tone="muted")
    else:
        for header_name in raw_headers_used:
            _print_wrapped(f"- {header_name}", indent=2)


def print_platform_section(scan_result):
    """
    Print platform detection output.
    """

    platform = scan_result["platform"]
    platform_finding = _first_finding(scan_result, category="Platform")

    _print_section_heading("PLATFORM DETECTION")
    _print_kv(
        "Detected Platform",
        platform.get("name") if platform.get("detected") else "Unknown",
        tone="highlight",
    )
    _print_kv("Confidence", _format_capitalized(platform.get("confidence"), "None"))

    if platform.get("evidence"):
        print(_style("Evidence:", BOLD, FG_MAGENTA))
        for evidence in platform["evidence"]:
            _print_wrapped(f"- {evidence}", indent=2)

    if platform_finding and platform_finding.get("recommendation"):
        _print_block("Operational Note", platform_finding["recommendation"], tone="note")


def print_html_section(scan_result):
    """
    Print lightweight HTML metadata.
    """

    html = scan_result["html"]

    _print_section_heading("HTML METADATA")
    _print_kv("Title Present", _format_bool(html.get("title_present")), tone="status")
    _print_kv("Title", _render_text(html.get("title")))
    _print_kv(
        "Meta Description Present",
        _format_bool(html.get("meta_description_present")),
        tone="status",
    )
    _print_kv("Canonical Present", _format_bool(html.get("canonical_present")), tone="status")
    _print_kv("Canonical URL", _render_text(html.get("canonical_url")), tone="url")
    _print_kv("Viewport Present", _format_bool(html.get("viewport_present")), tone="status")
    _print_kv("Charset", _render_text(html.get("charset")))
    _print_kv("Generator", _render_text(html.get("generator")))
    _print_kv("Script Count", html.get("script_count", 0))
    _print_kv("Stylesheet Count", html.get("stylesheet_count", 0))


def print_performance_section(scan_result):
    """
    Print lightweight performance indicators.
    """

    performance = scan_result["performance"]

    _print_section_heading("PERFORMANCE INDICATORS")
    _print_kv("Response Time", _format_seconds(performance.get("response_time_seconds")))
    _print_kv("Payload Size", _format_payload_size(performance.get("size_bytes")))
    _print_kv(
        "Page Weight Classification",
        _render_text(performance.get("page_weight_classification")),
        tone="highlight",
    )
    _print_kv(
        "Compression Enabled",
        _format_bool(performance.get("compression_enabled")),
        tone="status",
    )
    _print_kv(
        "Cache Configured",
        _format_bool(performance.get("cache_configured")),
        tone="status",
    )
    _print_block(
        "Performance Note",
        "This is not a full performance test. It is based on the primary "
        "response observed during this inspection.",
        tone="muted",
    )


def print_findings_section(scan_result):
    """
    Print all structured findings in their detailed consultant-style format.
    """

    findings = scan_result.get("findings", [])
    evidence_lookup = _build_evidence_lookup(scan_result)

    _print_section_heading("OPERATIONAL FINDINGS")
    if not findings:
        _print_wrapped(
            "No major operational issues were identified from the inspected response.",
            tone="muted",
        )
        return

    for index, finding in enumerate(findings):
        if index > 0:
            _print_rule("=")

        severity_tag = _severity_style(finding["risk_contribution"])
        title_text = _style(finding["title"], BOLD, FG_WHITE)
        print(f"[{severity_tag}] {title_text}")

        if finding.get("evidence_ids"):
            print(_style("Evidence:", BOLD, FG_MAGENTA))
            for evidence_id in finding["evidence_ids"]:
                evidence = evidence_lookup.get(evidence_id)
                if evidence is None:
                    continue
                evidence_text = f"- {evidence['name']}: {_format_evidence_value(evidence)}"
                _print_wrapped(evidence_text, indent=2)

        _print_block("Observation", finding["observation"])
        _print_block("Interpretation", finding["interpretation"], tone="muted")
        if finding.get("recommendation"):
            _print_block("Recommendation", finding["recommendation"], tone="note")


def print_recommendations_section(scan_result):
    """
    Print grouped recommendations derived from findings.
    """

    grouped_recommendations = _group_recommendations(scan_result.get("recommendations", []))

    _print_section_heading("RECOMMENDATIONS")
    if not any(grouped_recommendations.values()):
        _print_wrapped(
            "No major configuration recommendations were generated from the observed response.",
            tone="muted",
        )
        return

    label_map = {
        "High": "High Priority",
        "Medium": "Medium Priority",
        "Low": "Low Priority",
        "Informational": "Informational",
    }

    first_group = True
    for priority in ("High", "Medium", "Low", "Informational"):
        recommendations = grouped_recommendations.get(priority, [])
        if not recommendations:
            continue

        if not first_group:
            print()
        first_group = False
        print(_style(f"{label_map[priority]}:", BOLD, FG_MAGENTA))
        for recommendation in recommendations:
            recommendation_text = f"- {recommendation['message']}"
            _print_wrapped(recommendation_text, indent=2, tone="note")


def print_raw_evidence_summary(scan_result):
    """
    Print a concise raw-evidence summary near the end of the report.
    """

    connectivity = scan_result["connectivity"]
    target = scan_result["target"]
    response = scan_result["response"]
    tls = scan_result["tls"]
    raw_headers = scan_result["headers"].get("raw", {})

    _print_section_heading("RAW EVIDENCE SUMMARY")
    _print_kv("Final URL", target.get("final_url") or "Not reached", tone="url")
    _print_kv("Status Code", _render_text(connectivity.get("status_code")), tone="status")
    _print_kv("Redirect Count", connectivity.get("redirect_count", 0))
    _print_kv("Payload Size", _format_payload_size(response.get("size_bytes")))
    if not tls.get("checked"):
        tls_status = "Not checked"
    elif tls.get("valid"):
        tls_status = "Valid"
    else:
        tls_status = "Invalid or not verified"
    _print_kv("TLS Status", tls_status, tone="status")
    print(_style("Raw Headers Observed:", BOLD, FG_MAGENTA))
    if not raw_headers:
        _print_wrapped("None observed", indent=2, tone="muted")
        return

    for header_name, value in sorted(raw_headers.items(), key=lambda item: item[0].lower()):
        _print_kv(header_name, value)


def print_report(scan_result):
    """
    Render a ScanResult object to stdout.
    """

    connectivity = scan_result["connectivity"]

    _print_report_title()
    print_executive_summary(scan_result)
    print_target_section(scan_result)
    print_connectivity_section(scan_result)
    print_tls_section(scan_result)

    if connectivity.get("reachable"):
        print_response_section(scan_result)
        print_header_overview(scan_result)
        print_header_categories(scan_result)
        print_cookie_section(scan_result)
        print_cache_section(scan_result)
        print_compression_section(scan_result)
        print_infrastructure_section(scan_result)
        print_platform_section(scan_result)
        print_html_section(scan_result)
        print_performance_section(scan_result)

    print_findings_section(scan_result)
    print_recommendations_section(scan_result)
    print_raw_evidence_summary(scan_result)
