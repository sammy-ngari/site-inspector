"""
Application entry point.

Coordinates scan execution and report generation.
"""

import argparse
import sys
from scanner import (
    basic_check,
    security_headers,
    ssl_check,
    detect_cms,
    compression_check,
    cache_analysis,
    cookie_security,
    server_fingerprint
)
from report import print_report

VERSION = "v1.1"

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
        help="Domain name to scan (e.g., example.com)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Display version information and exit",
    )
    return parser.parse_args()

def main():

    print_banner()

    args = parse_arguments()

    # If --version is used, print version and exit
    if args.version:
        print(f"Site Inspector {VERSION}")
        sys.exit(0)

    # Determine domain
    if args.domain:
        domain = args.domain
    else:
        domain = input("Enter a domain to scan (e.g., example.com): ")

    basic = basic_check(domain)

    if not basic["reachable"]:
        print("Could not reach website.")
        sys.exit(1)

    ssl_data = ssl_check(domain.replace("https://", "").replace("http://", "").split("/")[0])
    headers = security_headers(basic["headers"])
    cms = detect_cms(basic["content"])
    compression = compression_check(basic["headers"])
    cache = cache_analysis(basic["headers"])
    cookies = cookie_security(basic["headers"])
    infra = server_fingerprint(basic["headers"])

    print_report(domain, basic, ssl_data, headers, cms, compression, cache, cookies, infra)

if __name__ == "__main__":
    main()