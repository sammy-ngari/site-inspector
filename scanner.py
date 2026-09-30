"""
Data collection layer.

Extracts measurable attributes from HTTP responses,
TLS metadata, and HTML content.
"""

import re
import socket
import ssl
import time
from datetime import datetime, timezone
from html import unescape
from http.cookies import CookieError, SimpleCookie

from knowledge_base import HEADER_CATEGORIES, HEADER_KNOWLEDGE_BASE
from utils import REQUEST_TIMEOUT_SECONDS, extract_hostname, fetch_site, normalize_url

PAGE_WEIGHT_SMALL_KB = 500
PAGE_WEIGHT_LARGE_KB = 2048
RECOGNIZED_COMPRESSION_METHODS = ("br", "gzip", "deflate", "zstd")
HEADER_CATEGORY_KEYS = tuple(HEADER_CATEGORIES.keys())
CATEGORY_NAME_TO_KEY = {
    display_name: category_key
    for category_key, display_name in HEADER_CATEGORIES.items()
}


def _normalize_header_lookup(headers):
    """
    Build a case-insensitive lookup table while preserving raw header input elsewhere.
    """

    return {header_name.lower(): value for header_name, value in headers.items()}


def _build_empty_header_categories():
    """
    Create stable header category buckets for the v1.2 data model.
    """

    return {category_name: [] for category_name in HEADER_CATEGORY_KEYS}


def _build_empty_cookie_summary():
    """
    Create a stable cookie summary object.
    """

    return {
        "total": 0,
        "secure_count": 0,
        "httponly_count": 0,
        "samesite_count": 0,
        "missing_secure_count": 0,
        "missing_httponly_count": 0,
        "missing_samesite_count": 0,
    }


def _build_error(component, message, exception_type):
    """
    Convert recoverable collector errors into structured error objects.
    """

    return {
        "component": component,
        "message": message,
        "recoverable": True,
        "exception_type": exception_type,
    }


def _parse_certificate_datetime(value):
    """
    Parse TLS certificate date strings into timezone-aware datetime objects.
    """

    if not value:
        return None, None

    parsed_value = datetime.strptime(value, "%b %d %H:%M:%S %Y %Z").replace(
        tzinfo=timezone.utc
    )
    iso_value = parsed_value.isoformat().replace("+00:00", "Z")
    return parsed_value, iso_value


def _extract_certificate_name(name_parts):
    """
    Flatten certificate issuer or subject tuples into readable strings.
    """

    values = []
    common_name = None

    for part in name_parts:
        for key, value in part:
            values.append(value)
            if key == "commonName" and common_name is None:
                common_name = value

    return common_name or ", ".join(values) or None


def _extract_html_match(pattern, content):
    """
    Return the first matching HTML metadata value using a simple regex.
    """

    match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
    if not match:
        return None

    return unescape(match.group(1).strip())


def _extract_meta_content(content, meta_name):
    """
    Extract the content attribute from a named meta tag.
    """

    patterns = (
        rf'<meta[^>]+name=["\']{re.escape(meta_name)}["\'][^>]+content=["\'](.*?)["\']',
        rf'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']{re.escape(meta_name)}["\']',
    )

    for pattern in patterns:
        extracted_value = _extract_html_match(pattern, content)
        if extracted_value is not None:
            return extracted_value

    return None


def _extract_link_href(content, rel_value):
    """
    Extract the href attribute from a link tag.
    """

    patterns = (
        rf'<link[^>]+rel=["\']{re.escape(rel_value)}["\'][^>]+href=["\'](.*?)["\']',
        rf'<link[^>]+href=["\'](.*?)["\'][^>]+rel=["\']{re.escape(rel_value)}["\']',
    )

    for pattern in patterns:
        extracted_value = _extract_html_match(pattern, content)
        if extracted_value is not None:
            return extracted_value

    return None


def _parse_cache_directives(cache_control):
    """
    Parse a Cache-Control string into a simple directive dictionary.
    """

    directives = {
        "max_age": None,
        "no_cache": False,
        "no_store": False,
        "public": False,
        "private": False,
        "must_revalidate": False,
    }

    if not cache_control:
        return directives

    for directive in cache_control.split(","):
        cleaned_directive = directive.strip().lower()
        if "=" in cleaned_directive:
            directive_name, raw_value = cleaned_directive.split("=", 1)
        else:
            directive_name, raw_value = cleaned_directive, None

        if directive_name == "max-age" and raw_value is not None:
            try:
                directives["max_age"] = int(raw_value.strip('"'))
            except ValueError:
                directives["max_age"] = None
        elif directive_name == "no-cache":
            directives["no_cache"] = True
        elif directive_name == "no-store":
            directives["no_store"] = True
        elif directive_name == "public":
            directives["public"] = True
        elif directive_name == "private":
            directives["private"] = True
        elif directive_name == "must-revalidate":
            directives["must_revalidate"] = True

    return directives


def _split_set_cookie_header(cookie_header):
    """
    Split a combined Set-Cookie header into individual cookie strings.
    """

    return [
        cookie_value.strip()
        for cookie_value in re.split(r", (?=[^ ;,]+=)", cookie_header)
        if cookie_value.strip()
    ]


def _fallback_cookie_entry(raw_cookie):
    """
    Preserve cookie evidence even when standard parsing is incomplete.
    """

    cookie_name_match = re.match(r"\s*([^=;\s]+)", raw_cookie)
    samesite_match = re.search(r"samesite=([^;,\s]+)", raw_cookie, re.IGNORECASE)
    max_age_match = re.search(r"max-age=([^;,\s]+)", raw_cookie, re.IGNORECASE)

    max_age = None
    if max_age_match:
        try:
            max_age = int(max_age_match.group(1))
        except ValueError:
            max_age = None

    domain_match = re.search(r"domain=([^;,\s]+)", raw_cookie, re.IGNORECASE)
    path_match = re.search(r"path=([^;,\s]+)", raw_cookie, re.IGNORECASE)
    expires_match = re.search(r"expires=([^;]+)", raw_cookie, re.IGNORECASE)

    return {
        "name": cookie_name_match.group(1) if cookie_name_match else "Unknown",
        "secure": "secure" in raw_cookie.lower(),
        "httponly": "httponly" in raw_cookie.lower(),
        "samesite": samesite_match.group(1) if samesite_match else None,
        "path": path_match.group(1) if path_match else None,
        "domain": domain_match.group(1) if domain_match else None,
        "expires": expires_match.group(1).strip() if expires_match else None,
        "max_age": max_age,
        "raw": raw_cookie,
    }


def _build_cookie_entry(morsel, raw_cookie):
    """
    Convert a parsed morsel into a cookie evidence object.
    """

    max_age = morsel["max-age"] or None
    if max_age is not None:
        try:
            max_age = int(max_age)
        except ValueError:
            max_age = None

    return {
        "name": morsel.key,
        "secure": bool(morsel["secure"]),
        "httponly": bool(morsel["httponly"]),
        "samesite": morsel["samesite"] or None,
        "path": morsel["path"] or None,
        "domain": morsel["domain"] or None,
        "expires": morsel["expires"] or None,
        "max_age": max_age,
        "raw": raw_cookie,
    }


def _summarize_cookies(cookies):
    """
    Count common cookie security attributes for reporting and risk review.
    """

    summary = _build_empty_cookie_summary()
    summary["total"] = len(cookies)
    summary["secure_count"] = sum(1 for cookie in cookies if cookie["secure"])
    summary["httponly_count"] = sum(1 for cookie in cookies if cookie["httponly"])
    summary["samesite_count"] = sum(1 for cookie in cookies if cookie["samesite"])
    summary["missing_secure_count"] = summary["total"] - summary["secure_count"]
    summary["missing_httponly_count"] = summary["total"] - summary["httponly_count"]
    summary["missing_samesite_count"] = summary["total"] - summary["samesite_count"]
    return summary


def _detect_cms_marker(content):
    """
    Return a CMS name and evidence string when a known marker is present.
    """

    lowered_content = content.lower()
    markers = (
        ("WordPress", "wp-content", "wp-content marker found in HTML", "medium"),
        ("WordPress", "wp-json", "wp-json marker found in HTML", "medium"),
        ("Shopify", "cdn.shopify.com", "Shopify CDN marker found in HTML", "medium"),
        ("Wix", "wixstatic.com", "Wix asset marker found in HTML", "medium"),
        ("Drupal", "/sites/default/", "Drupal path marker found in HTML", "medium"),
        ("Joomla", "/components/com_", "Joomla component marker found in HTML", "medium"),
    )

    for name, marker, evidence, confidence in markers:
        if marker in lowered_content:
            return name, evidence, confidence

    return "Unknown", None, "none"


def _classify_page_weight(size_bytes):
    """
    Convert a raw byte size into the v1.2 page weight buckets.
    """

    if size_bytes is None:
        return "Unknown"

    size_kb = size_bytes / 1024
    if size_kb < PAGE_WEIGHT_SMALL_KB:
        return "Small"
    if size_kb <= PAGE_WEIGHT_LARGE_KB:
        return "Moderate"
    return "Large"


def basic_check(domain):
    """
    Perform baseline connectivity and response analysis.

    Measures:
        - Reachability
        - Final URL
        - HTTP status code
        - Response time
        - Redirect count
        - Headers
        - Body content
        - Payload size

    Returns
    -------
    dict
        Structured response data for downstream processing.
    """

    start = time.perf_counter()
    data = fetch_site(domain)
    end = time.perf_counter()
    response_time = round(end - start, 2)

    if not data["ok"]:
        return {
            "reachable": False,
            "input_url": domain,
            "normalized_url": data.get("normalized_url"),
            "final_url": None,
            "status_code": None,
            "response_time": None,
            "redirects": 0,
            "redirect_chain": [],
            "headers": {},
            "content": "",
            "size": None,
            "error": data.get("error"),
            "error_type": data.get("error_type"),
        }

    return {
        "reachable": True,
        "input_url": domain,
        "normalized_url": data["normalized_url"],
        "final_url": data["url"],
        "status_code": data["status_code"],
        "response_time": response_time,
        "redirects": len(data["history"]),
        "redirect_chain": data["history"],
        "headers": data["headers"],
        "content": data["content"],
        "size": data["size"],
        "error": None,
        "error_type": None,
    }


def security_headers(headers):
    """
    Check presence of selected security-related HTTP headers.

    Parameters
    ----------
    headers : Mapping
        Response headers from the HTTP request.

    Returns
    -------
    dict
        Mapping of header name → "Present" | "Missing".
    """

    important_headers = {
        "Strict-Transport-Security": "HSTS",
        "Content-Security-Policy": "CSP",
        "X-Content-Type-Options": "X-Content-Type-Options",
        "X-Frame-Options": "X-Frame-Options",
        "Referrer-Policy": "Referrer-Policy",
    }

    results = {}
    normalized_headers = _normalize_header_lookup(headers)

    for header_name, display_name in important_headers.items():
        results[display_name] = (
            "Present" if header_name.lower() in normalized_headers else "Missing"
        )

    return results


def _csp_has_frame_ancestors(normalized_headers):
    """
    Detect whether the observed CSP includes a frame-ancestors directive.
    """

    csp_entry = normalized_headers.get("content-security-policy")
    if not csp_entry:
        return False

    csp_value = csp_entry.get("value") or ""
    return "frame-ancestors" in csp_value.lower()


def _build_known_header_entry(metadata, normalized_name, value, present):
    """
    Convert known header metadata into a categorized header entry.
    """

    interpretation = (
        metadata["interpretation_present"]
        if present
        else metadata["interpretation_missing"]
    )
    recommendation = (
        metadata["recommendation_present"]
        if present
        else metadata["recommendation_missing"]
    )
    risk_contribution = (
        metadata["risk_if_present"] if present else metadata["risk_if_missing"]
    )

    return {
        "name": metadata["canonical_name"],
        "normalized_name": normalized_name,
        "value": value,
        "present": present,
        "known": True,
        "category": metadata["category"],
        "deprecated": metadata["deprecated"],
        "purpose": metadata["purpose"],
        "interpretation": interpretation,
        "recommendation": recommendation,
        "risk_contribution": risk_contribution,
        "expected": metadata["expected"],
    }


def _build_unknown_header_entry(original_name, normalized_name, value):
    """
    Convert an unknown observed header into the required unclassified shape.
    """

    return {
        "name": original_name,
        "normalized_name": normalized_name,
        "value": value,
        "present": True,
        "known": False,
        "category": HEADER_CATEGORIES["vendor_specific_unclassified"],
        "deprecated": False,
        "purpose": None,
        "interpretation": "Header observed but not classified by Site Inspector.",
        "recommendation": None,
        "risk_contribution": "Informational",
    }


def _should_include_missing_header(normalized_name, metadata, normalized_headers, final_url):
    """
    Decide whether a missing known header should appear as expected missing evidence.
    """

    if metadata["expected"] != "present":
        return False

    if normalized_name == "strict-transport-security":
        return (final_url or "").startswith("https://")

    if normalized_name == "x-frame-options" and _csp_has_frame_ancestors(normalized_headers):
        return False

    return True


def _sort_header_entries(entries):
    """
    Keep category entries deterministic for stable reports.
    """

    return sorted(
        entries,
        key=lambda entry: (
            entry["name"].lower(),
            0 if entry["present"] else 1,
        ),
    )


def compression_check(headers):
    """
    Determine whether HTTP compression is enabled from Content-Encoding.
    """

    normalized_headers = _normalize_header_lookup(headers)
    content_encoding = normalized_headers.get("content-encoding")

    if not content_encoding:
        return {
            "enabled": False,
            "method": None,
            "content_encoding": None,
        }

    lowered_encoding = content_encoding.lower()
    for method in RECOGNIZED_COMPRESSION_METHODS:
        if method in lowered_encoding:
            return {
                "enabled": True,
                "method": method,
                "content_encoding": content_encoding,
            }

    return {
        "enabled": True,
        "method": lowered_encoding,
        "content_encoding": content_encoding,
    }


def cache_analysis(headers):
    """
    Evaluate cache and freshness headers from the primary response.
    """

    normalized_headers = _normalize_header_lookup(headers)
    cache_control = normalized_headers.get("cache-control")
    expires = normalized_headers.get("expires")
    etag = normalized_headers.get("etag")
    last_modified = normalized_headers.get("last-modified")
    vary = normalized_headers.get("vary")

    return {
        "cache_control": cache_control,
        "expires": expires,
        "etag": etag,
        "last_modified": last_modified,
        "vary": vary,
        "configured": bool(cache_control or expires or etag or last_modified),
        "directives": _parse_cache_directives(cache_control),
    }


def cookie_security(headers):
    """
    Inspect Set-Cookie headers and return structured cookie evidence.
    """

    normalized_headers = _normalize_header_lookup(headers)
    cookie_header = normalized_headers.get("set-cookie")

    if not cookie_header:
        return {
            "present": False,
            "cookies": [],
            "summary": _build_empty_cookie_summary(),
        }, []

    cookies = []
    errors = []

    for raw_cookie in _split_set_cookie_header(cookie_header):
        try:
            parsed_cookie = SimpleCookie()
            parsed_cookie.load(raw_cookie)
        except CookieError as exc:
            cookies.append(_fallback_cookie_entry(raw_cookie))
            errors.append(
                _build_error("cookies", f"Cookie parsing fallback used: {exc}", "CookieError")
            )
            continue

        if not parsed_cookie:
            cookies.append(_fallback_cookie_entry(raw_cookie))
            errors.append(
                _build_error(
                    "cookies",
                    "Cookie parsing fallback used because no morsels were produced.",
                    "CookieParseFallback",
                )
            )
            continue

        for morsel in parsed_cookie.values():
            cookies.append(_build_cookie_entry(morsel, raw_cookie))

    return {
        "present": True,
        "cookies": cookies,
        "summary": _summarize_cookies(cookies),
    }, errors


def server_fingerprint(headers):
    """
    Extract public infrastructure indicators from response headers.
    """

    normalized_headers = _normalize_header_lookup(headers)
    alt_svc = normalized_headers.get("alt-svc", "")

    raw_headers_used = []
    server = normalized_headers.get("server")
    x_powered_by = normalized_headers.get("x-powered-by")
    via = normalized_headers.get("via")

    if server:
        raw_headers_used.append("Server")
    if x_powered_by:
        raw_headers_used.append("X-Powered-By")
    if via:
        raw_headers_used.append("Via")

    cdn_indicators = []
    if normalized_headers.get("cf-ray"):
        cdn_indicators.append(
            {
                "provider": "Cloudflare",
                "evidence": "CF-Ray header observed",
                "confidence": "high",
            }
        )
        raw_headers_used.append("CF-Ray")
    if normalized_headers.get("cf-cache-status"):
        cdn_indicators.append(
            {
                "provider": "Cloudflare",
                "evidence": "CF-Cache-Status header observed",
                "confidence": "high",
            }
        )
        raw_headers_used.append("CF-Cache-Status")

    proxy_indicators = []
    if via:
        proxy_indicators.append(
            {
                "provider": "Proxy or intermediary",
                "evidence": "Via header observed",
                "confidence": "medium",
            }
        )

    edge_indicators = []
    if normalized_headers.get("x-cache"):
        edge_indicators.append(
            {
                "provider": "Edge cache",
                "evidence": "X-Cache header observed",
                "confidence": "medium",
            }
        )
        raw_headers_used.append("X-Cache")
    if normalized_headers.get("x-served-by"):
        edge_indicators.append(
            {
                "provider": "Edge platform",
                "evidence": "X-Served-By header observed",
                "confidence": "medium",
            }
        )
        raw_headers_used.append("X-Served-By")

    return {
        "server": server,
        "x_powered_by": x_powered_by,
        "via": via,
        "cdn_indicators": cdn_indicators,
        "proxy_indicators": proxy_indicators,
        "edge_indicators": edge_indicators,
        "http3_hint": "h3" in alt_svc.lower(),
        "raw_headers_used": raw_headers_used,
    }


def _build_skipped_tls_result():
    """
    Return a deterministic TLS object when the site is unreachable.
    """

    return {
        "checked": False,
        "valid": False,
        "days_until_expiry": None,
        "not_before": None,
        "not_after": None,
        "issuer": None,
        "subject": None,
        "serial_number": None,
        "error": "TLS check skipped because the site was unreachable.",
        "exception_type": "TLSCheckSkipped",
    }


def ssl_check(domain):
    """
    Retrieve TLS certificate metadata and calculate remaining validity.
    """

    if not domain:
        return {
            "checked": False,
            "valid": False,
            "days_until_expiry": None,
            "not_before": None,
            "not_after": None,
            "issuer": None,
            "subject": None,
            "serial_number": None,
            "error": "A hostname was not available for TLS inspection.",
            "exception_type": "HostnameError",
        }

    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as secure_socket:
                certificate = secure_socket.getpeercert()
                not_before_dt, not_before = _parse_certificate_datetime(
                    certificate.get("notBefore")
                )
                not_after_dt, not_after = _parse_certificate_datetime(
                    certificate.get("notAfter")
                )

                days_until_expiry = None
                if not_after_dt is not None:
                    days_until_expiry = (not_after_dt - datetime.now(timezone.utc)).days

                return {
                    "checked": True,
                    "valid": True,
                    "days_until_expiry": days_until_expiry,
                    "not_before": not_before,
                    "not_after": not_after,
                    "issuer": _extract_certificate_name(certificate.get("issuer", ())),
                    "subject": _extract_certificate_name(certificate.get("subject", ())),
                    "serial_number": certificate.get("serialNumber"),
                    "error": None,
                    "exception_type": None,
                }

    except (
        socket.gaierror,
        socket.timeout,
        TimeoutError,
        ConnectionRefusedError,
        ssl.SSLError,
        OSError,
        ValueError,
        KeyError,
    ) as exc:
        return {
            "checked": True,
            "valid": False,
            "days_until_expiry": None,
            "not_before": None,
            "not_after": None,
            "issuer": None,
            "subject": None,
            "serial_number": None,
            "error": str(exc) or "TLS inspection could not be completed.",
            "exception_type": exc.__class__.__name__,
        }


def detect_cms(content):
    """
    Perform heuristic CMS detection based on HTML markers.
    """

    cms_name, _, _ = _detect_cms_marker(content)
    return cms_name


def platform_analysis(content):
    """
    Convert CMS markers into a structured platform result.
    """

    cms_name, evidence, confidence = _detect_cms_marker(content)
    if cms_name == "Unknown":
        return {
            "detected": False,
            "name": "Unknown",
            "confidence": "none",
            "evidence": [],
        }

    return {
        "detected": True,
        "name": cms_name,
        "confidence": confidence,
        "evidence": [evidence],
    }


def html_metadata_analysis(content):
    """
    Extract lightweight metadata from the returned HTML response body.
    """

    if not content:
        return {
            "title": None,
            "title_present": False,
            "meta_description_present": False,
            "meta_description": None,
            "canonical_present": False,
            "canonical_url": None,
            "viewport_present": False,
            "charset": None,
            "generator": None,
            "script_count": 0,
            "stylesheet_count": 0,
        }

    title = _extract_html_match(r"<title[^>]*>(.*?)</title>", content)
    meta_description = _extract_meta_content(content, "description")
    canonical_url = _extract_link_href(content, "canonical")
    generator = _extract_meta_content(content, "generator")
    charset = _extract_html_match(r'<meta[^>]+charset=["\']?([^"\'>\s]+)', content)

    return {
        "title": title,
        "title_present": title is not None,
        "meta_description_present": meta_description is not None,
        "meta_description": meta_description,
        "canonical_present": canonical_url is not None,
        "canonical_url": canonical_url,
        "viewport_present": _extract_meta_content(content, "viewport") is not None,
        "charset": charset,
        "generator": generator,
        "script_count": len(re.findall(r"<script\b", content, re.IGNORECASE)),
        "stylesheet_count": len(
            re.findall(
                r'<link[^>]+rel=["\']stylesheet["\']',
                content,
                re.IGNORECASE,
            )
        ),
    }


def build_headers_result(raw_headers, reachable, final_url):
    """
    Convert raw headers into the v1.2 header container shape.
    """

    normalized_headers = {}
    for original_name, value in raw_headers.items():
        normalized_name = original_name.lower()
        normalized_headers[normalized_name] = {
            "original_name": original_name,
            "value": value,
        }

    categorized_headers = _build_empty_header_categories()
    security_checks = security_headers(raw_headers) if reachable else {}
    known_observed = 0
    unknown_observed = 0
    deprecated_observed = 0
    expected_missing_count = 0

    for original_name, value in sorted(raw_headers.items(), key=lambda item: item[0].lower()):
        normalized_name = original_name.lower()
        metadata = HEADER_KNOWLEDGE_BASE.get(normalized_name)

        if metadata:
            known_observed += 1
            if metadata["deprecated"]:
                deprecated_observed += 1
            category_key = CATEGORY_NAME_TO_KEY[metadata["category"]]
            categorized_headers[category_key].append(
                _build_known_header_entry(metadata, normalized_name, value, True)
            )
        else:
            unknown_observed += 1
            categorized_headers["vendor_specific_unclassified"].append(
                _build_unknown_header_entry(original_name, normalized_name, value)
            )

    if reachable:
        for normalized_name, metadata in sorted(
            HEADER_KNOWLEDGE_BASE.items(),
            key=lambda item: item[1]["canonical_name"].lower(),
        ):
            if normalized_name in normalized_headers:
                continue

            if not _should_include_missing_header(
                normalized_name,
                metadata,
                normalized_headers,
                final_url,
            ):
                continue

            category_key = CATEGORY_NAME_TO_KEY[metadata["category"]]
            categorized_headers[category_key].append(
                _build_known_header_entry(metadata, normalized_name, None, False)
            )
            expected_missing_count += 1

    for category_key in categorized_headers:
        categorized_headers[category_key] = _sort_header_entries(
            categorized_headers[category_key]
        )

    return {
        "raw": raw_headers,
        "normalized": normalized_headers,
        "categorized": categorized_headers,
        "summary": {
            "total_observed": len(raw_headers),
            "known_observed": known_observed,
            "unknown_observed": unknown_observed,
            "expected_known_missing": expected_missing_count,
            "deprecated_observed": deprecated_observed,
        },
        "security_checks": security_checks,
    }


def response_analysis(connectivity, headers_result, compression_result, content):
    """
    Build the final HTTP response summary from collected evidence.
    """

    normalized_headers = headers_result["normalized"]
    content_type = normalized_headers.get("content-type", {}).get("value")
    content_length = normalized_headers.get("content-length", {}).get("value")

    return {
        "status_code": connectivity["status_code"],
        "content_type": content_type,
        "content_length": content_length,
        "size_bytes": connectivity["size"],
        "encoding": compression_result["content_encoding"],
        "body_present": bool(content),
        "body_sample": None,
    }


def performance_analysis(connectivity, compression_result, cache_result):
    """
    Derive lightweight performance indicators from the collected response.
    """

    size_bytes = connectivity["size"]
    size_kb = None
    if size_bytes is not None:
        size_kb = round(size_bytes / 1024, 1)

    return {
        "response_time_seconds": connectivity["response_time"],
        "size_bytes": size_bytes,
        "size_kb": size_kb,
        "page_weight_classification": _classify_page_weight(size_bytes),
        "compression_enabled": compression_result["enabled"],
        "cache_configured": cache_result["configured"],
    }


def collect_scan_result(domain, project_version, project_description):
    """
    Collect all currently supported evidence into the canonical v1.2 ScanResult shape.
    """

    connectivity_data = basic_check(domain)
    raw_headers = connectivity_data["headers"]
    hostname = extract_hostname(connectivity_data["normalized_url"] or domain)
    if connectivity_data["reachable"]:
        tls_hostname = extract_hostname(connectivity_data["final_url"] or domain)
        if tls_hostname:
            hostname = tls_hostname
        tls_result = ssl_check(tls_hostname)
    else:
        tls_result = _build_skipped_tls_result()
    headers_result = build_headers_result(
        raw_headers,
        connectivity_data["reachable"],
        connectivity_data["final_url"],
    )
    cache_result = cache_analysis(raw_headers)
    compression_result = compression_check(raw_headers)
    cookie_result, cookie_errors = cookie_security(raw_headers)
    infrastructure_result = server_fingerprint(raw_headers)
    platform_result = platform_analysis(connectivity_data["content"])
    html_result = html_metadata_analysis(connectivity_data["content"])
    response_result = response_analysis(
        connectivity_data,
        headers_result,
        compression_result,
        connectivity_data["content"],
    )
    performance_result = performance_analysis(
        connectivity_data,
        compression_result,
        cache_result,
    )

    errors = []
    if connectivity_data["error"]:
        errors.append(
            _build_error(
                "connectivity",
                connectivity_data["error"],
                connectivity_data["error_type"],
            )
        )
    if tls_result["error"]:
        errors.append(
            _build_error("tls", tls_result["error"], tls_result["exception_type"])
        )
    errors.extend(cookie_errors)

    return {
        "project": {
            "name": "Site Inspector",
            "version": project_version,
            "description": project_description,
        },
        "target": {
            "input": domain,
            "normalized_url": connectivity_data["normalized_url"] or normalize_url(domain),
            "hostname": hostname,
            "final_url": connectivity_data["final_url"],
        },
        "request": {
            "method": "GET",
            "timeout_seconds": REQUEST_TIMEOUT_SECONDS,
            "redirects_enabled": True,
            "single_request_model": True,
            "user_agent": None,
        },
        "connectivity": {
            "reachable": connectivity_data["reachable"],
            "status_code": connectivity_data["status_code"],
            "response_time_seconds": connectivity_data["response_time"],
            "redirect_count": connectivity_data["redirects"],
            "redirect_chain": connectivity_data["redirect_chain"],
        },
        "tls": tls_result,
        "response": response_result,
        "headers": headers_result,
        "cookies": cookie_result,
        "cache": cache_result,
        "compression": compression_result,
        "infrastructure": infrastructure_result,
        "platform": platform_result,
        "html": html_result,
        "performance": performance_result,
        "evidence": [],
        "observations": [],
        "findings": [],
        "recommendations": [],
        "risk": {},
        "errors": errors,
    }
