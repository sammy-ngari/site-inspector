"""
Application entry point.

Coordinates scan execution and report generation.
"""

import argparse
import json
import sys

from report import print_report
from risk import analyze_risk
from scanner import collect_scan_result
from utils import REQUEST_TIMEOUT_SECONDS, extract_hostname, normalize_url

VERSION = "v1.2"
DESCRIPTION = "Passive Website Configuration Auditor"


def print_banner():
    """
    Displays CLI header for the tool.
    Keeps branding minimal and professional.
    """
    print("=" * 60)
    print("SITE INSPECTOR".center(60))
    print("Passive Website Configuration Auditor".center(60))
    print(f"Version: {VERSION}".center(60))
    print("Created & Maintained by Sammy Ngari".center(60))
    print("=" * 60)
    print()


def parse_arguments():
    """
    Parses CLI arguments for Site Inspector.
    """

    parser = argparse.ArgumentParser(
        description="Site Inspector - Passive Website Configuration Auditor",
    )
    parser.add_argument(
        "--domain",
        nargs="?",
        help="Domain name to inspect (e.g., example.com)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Display version information and exit",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the complete structured scan result as JSON",
    )
    return parser.parse_args()


def _build_json_error_result(domain, error_message, exception_type):
    """
    Build a machine-readable fallback result for JSON-mode failures.
    """

    normalized_url = normalize_url(domain) if domain else None
    hostname = extract_hostname(normalized_url) if normalized_url else None

    return {
        "project": {
            "name": "Site Inspector",
            "version": VERSION,
            "description": DESCRIPTION,
        },
        "target": {
            "input": domain,
            "normalized_url": normalized_url,
            "hostname": hostname,
            "final_url": None,
        },
        "request": {
            "method": "GET",
            "timeout_seconds": REQUEST_TIMEOUT_SECONDS,
            "redirects_enabled": True,
            "single_request_model": True,
            "user_agent": None,
        },
        "connectivity": {
            "reachable": False,
            "status_code": None,
            "response_time_seconds": None,
            "redirect_count": 0,
            "redirect_chain": [],
        },
        "tls": {
            "checked": False,
            "valid": False,
            "days_until_expiry": None,
            "not_before": None,
            "not_after": None,
            "issuer": None,
            "subject": None,
            "serial_number": None,
            "error": error_message,
            "exception_type": exception_type,
        },
        "response": {
            "status_code": None,
            "content_type": None,
            "content_length": None,
            "size_bytes": None,
            "encoding": None,
            "body_present": False,
            "body_sample": None,
        },
        "headers": {
            "raw": {},
            "normalized": {},
            "categorized": {},
            "summary": {
                "total_observed": 0,
                "known_observed": 0,
                "unknown_observed": 0,
                "expected_known_missing": 0,
                "deprecated_observed": 0,
            },
            "security_checks": {},
        },
        "cookies": {
            "present": False,
            "cookies": [],
            "summary": {
                "total": 0,
                "secure_count": 0,
                "httponly_count": 0,
                "samesite_count": 0,
                "missing_secure_count": 0,
                "missing_httponly_count": 0,
                "missing_samesite_count": 0,
            },
        },
        "cache": {
            "cache_control": None,
            "expires": None,
            "etag": None,
            "last_modified": None,
            "vary": None,
            "configured": False,
            "directives": {
                "max_age": None,
                "no_cache": False,
                "no_store": False,
                "public": False,
                "private": False,
                "must_revalidate": False,
            },
        },
        "compression": {
            "enabled": False,
            "method": None,
            "content_encoding": None,
        },
        "infrastructure": {
            "server": None,
            "x_powered_by": None,
            "via": None,
            "cdn_indicators": [],
            "proxy_indicators": [],
            "edge_indicators": [],
            "http3_hint": False,
            "raw_headers_used": [],
        },
        "platform": {
            "detected": False,
            "name": "Unknown",
            "confidence": "none",
            "evidence": [],
        },
        "html": {
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
        },
        "performance": {
            "response_time_seconds": None,
            "size_bytes": None,
            "size_kb": None,
            "page_weight_classification": "Unknown",
            "compression_enabled": False,
            "cache_configured": False,
        },
        "evidence": [],
        "observations": [],
        "findings": [],
        "recommendations": [],
        "risk": {
            "level": "High",
            "score": 0,
            "summary": error_message,
            "contributors": [],
        },
        "errors": [
            {
                "component": "cli",
                "message": error_message,
                "recoverable": True,
                "exception_type": exception_type,
            }
        ],
    }


def _print_json_result(scan_result):
    """
    Emit a machine-readable JSON result without console formatting.
    """

    print(json.dumps(scan_result, indent=2))


def _run_inspection(domain):
    """
    Execute the shared inspection workflow and attach risk output.
    """

    scan_result = collect_scan_result(domain, VERSION, DESCRIPTION)
    scan_result["risk"] = analyze_risk(scan_result)
    return scan_result


def main():
    args = parse_arguments()

    if args.version:
        print(f"Site Inspector {VERSION}")
        return 0

    if not args.json:
        print_banner()

    if args.domain:
        domain = args.domain
    elif args.json:
        domain = ""
    else:
        domain = input("Enter a domain to inspect (e.g., example.com): ").strip()

    if args.json:
        if not domain:
            _print_json_result(
                _build_json_error_result(
                    domain,
                    "A domain is required when using JSON output.",
                    "ArgumentError",
                )
            )
            return 2

        try:
            scan_result = _run_inspection(domain)
        except Exception as exc:
            _print_json_result(
                _build_json_error_result(
                    domain,
                    str(exc) or "Inspection failed during JSON output generation.",
                    exc.__class__.__name__,
                )
            )
            return 1

        _print_json_result(scan_result)
        return 0 if scan_result["connectivity"]["reachable"] else 1

    scan_result = _run_inspection(domain)
    print_report(scan_result)
    return 0 if scan_result["connectivity"]["reachable"] else 1


if __name__ == "__main__":
    sys.exit(main())
