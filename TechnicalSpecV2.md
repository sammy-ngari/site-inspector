# Site Inspector Technical Design Specification (TDS)

**Volume II — System Architecture & Implementation Model**

**Document Version:** 1.0
**Project Version Covered:** Current v1.1 → Target v1.2
**Status:** Authoritative Engineering Specification
**Depends On:** Volume I — Project Constitution

---

# 1. Purpose of this Volume

This volume defines the technical architecture of Site Inspector.

Where Volume I defines the project philosophy, this volume defines how the software must be structured, how data must flow through the system, which modules own which responsibilities, and how Version 1.2 should evolve from the current Version 1.1 implementation.

This volume is intended to guide Codex or any future developer implementing, refactoring, extending, or reviewing the Site Inspector codebase.

The implementation must remain faithful to the principles established in Volume I.

The most important architectural rule is this:

Site Inspector must remain an evidence-first, passive, deterministic configuration intelligence engine.

---

# 2. Current Implementation Status

The current codebase represents **Site Inspector v1.1**.

Version 1.1 is functional and provides the foundation for Version 1.2.

It already includes the following files:

```text
main.py
utils.py
scanner.py
risk.py
report.py
requirements.txt
README.md
.gitignore
```

The current implementation should not be discarded. Version 1.2 must evolve from it incrementally.

Codex must not rewrite the entire project unless explicitly instructed.

---

# 3. Current v1.1 File Responsibilities

## 3.1 `main.py`

Current responsibility:

`main.py` acts as the application entry point.

It currently:

* displays the CLI banner,
* defines the project version,
* parses CLI arguments,
* accepts a domain through `--domain` or interactive prompt,
* coordinates scanner calls,
* passes collected data to the reporting layer,
* exits when the site is unreachable.

Current CLI support:

```bash
python main.py
python main.py --domain example.com
python main.py --version
```

Current architectural status:

`main.py` is conceptually correct. It should remain the orchestration layer.

Required v1.2 direction:

`main.py` should become thinner. It should orchestrate a single high-level scan workflow and pass the final structured result to the report layer.

It should not manually coordinate many independent variables indefinitely.

Target direction:

```python
scan_result = run_scan(domain)
report = build_report(scan_result)
print_report(report)
```

This does not require an immediate full rewrite, but v1.2 should move toward this structure.

---

## 3.2 `utils.py`

Current responsibility:

`utils.py` contains networking utilities.

It currently provides:

* URL normalization by adding `https://` when no scheme is provided,
* a primary HTTP GET request using `requests.get`,
* redirect following,
* response headers,
* response body,
* response size,
* redirect history,
* failure handling.

Current architectural status:

`utils.py` correctly owns the HTTP retrieval layer.

Required v1.2 direction:

`utils.py` must remain low-level. It must not interpret headers, calculate risk, detect CMS platforms, or format reports.

It may be expanded to include:

* `normalize_url()`
* `extract_hostname()`
* `fetch_site()`
* response error normalization
* request metadata extraction

It must not include:

* risk logic,
* report logic,
* header interpretation logic,
* CMS interpretation logic.

---

## 3.3 `scanner.py`

Current responsibility:

`scanner.py` acts as the evidence collection layer.

It currently provides:

* basic connectivity check,
* response time measurement,
* final URL extraction,
* status code extraction,
* redirect count extraction,
* security header presence check,
* compression check,
* cache analysis,
* cookie security check,
* server fingerprint extraction,
* TLS certificate check,
* CMS detection.

Current architectural status:

`scanner.py` is doing the correct kind of work, but it is becoming too broad.

Required v1.2 direction:

For v1.2, `scanner.py` may remain as a single file, but the specification should define the future modular structure.

The current scanner responsibilities should eventually split into smaller scanner modules.

Target future structure:

```text
scanner/
    __init__.py
    connectivity.py
    tls.py
    headers.py
    cookies.py
    cache.py
    compression.py
    cms.py
    html.py
    infrastructure.py
```

This split should not be forced immediately if it causes unnecessary disruption.

Codex should prefer incremental refactoring.

---

## 3.4 `risk.py`

Current responsibility:

`risk.py` interprets collected indicators and assigns an overall risk level.

It currently:

* assigns score points,
* produces a risk level,
* produces a list of issues.

Current architectural status:

`risk.py` is correctly separated from scanning and reporting. However, the current wording is too security-scanner-like in places and should be adjusted to match Site Inspector's consultant-style tone.

Required v1.2 direction:

`risk.py` should not directly depend on loose individual variables forever.

It should eventually accept a structured `scan_result` or a list of generated findings.

Target direction:

```python
risk_summary = analyze_risk(findings)
```

or:

```python
risk_summary = analyze_risk(scan_result)
```

Preferred long-term model:

Evidence generates observations.

Observations generate findings.

Findings contribute to risk.

Risk should not be calculated directly from raw headers where avoidable.

---

## 3.5 `report.py`

Current responsibility:

`report.py` formats collected data and risk analysis for console output.

It currently:

* prints report sections,
* handles unreachable sites,
* prints SSL information,
* prints platform information,
* prints security headers,
* prints compression and cache status,
* prints cookie security,
* prints infrastructure indicators,
* prints overall risk analysis.

Current architectural status:

`report.py` correctly owns presentation, but the output is currently flat and should evolve into a hierarchical report.

Required v1.2 direction:

`report.py` should render a structured report from a structured result.

It should not perform evidence collection.

It should not perform network requests.

It should not contain core risk scoring logic.

It may contain formatting decisions.

Target report structure:

```text
Executive Summary
Target & Request
Connectivity
Transport Security
HTTP Response
Headers
    Security & Browser Protection
    Caching & Freshness
    Compression & Transfer
    Cookies & Sessions
    CORS & Cross-Origin Access
    CDN / Proxy / Edge Infrastructure
    Server / Application Disclosure
    Protocol / Connection Behaviour
    Legacy / Deprecated Headers
    Vendor-Specific / Unclassified
Platform Detection
Performance Indicators
Operational Findings
Recommendations
Raw Evidence
```

---

## 3.6 `requirements.txt`

Current responsibility:

Defines Python package dependencies.

Current dependency stack:

```text
requests
certifi
charset-normalizer
idna
urllib3
```

Required v1.2 direction:

Keep dependencies minimal.

Do not add heavy external dependencies unless explicitly approved.

Version 1.2 should remain possible with the current dependency set and Python built-ins.

---

## 3.7 `README.md`

Current responsibility:

Provides public-facing project explanation, installation instructions, usage, and passive-use notice.

Current architectural status:

The README is useful but must be updated for Version 1.2.

Required v1.2 direction:

README should reflect:

* project identity,
* passive-only scope,
* single-request model,
* current version,
* CLI usage,
* configuration categories,
* what the tool does not do,
* ethical usage notice.

The README should not overpromise.

---

# 4. Required v1.1 → v1.2 Evolution

Version 1.2 must be an incremental improvement over Version 1.1.

Codex must treat Version 1.1 as the existing baseline and Version 1.2 as the planned target.

The following v1.1 elements must be preserved:

* CLI execution,
* `--domain` argument,
* `--version` argument,
* interactive fallback prompt,
* passive HTTP GET model,
* redirect following,
* response timing,
* TLS certificate inspection,
* CMS detection,
* response header capture,
* compression detection,
* cache analysis,
* cookie inspection,
* infrastructure hint extraction,
* risk analysis,
* console report.

Version 1.2 must add or improve:

* complete response header collection,
* header categorization,
* header knowledge base,
* evidence model,
* observation model,
* finding model,
* recommendation model,
* hierarchical report output,
* clearer consultant-style wording,
* deterministic interpretation rules,
* structured scan result object,
* improved error handling,
* README version consistency,
* current bug fixes.

---

# 5. Single Primary HTTP Request Model

The entire architecture depends on this rule.

Version 1.2 must use exactly one primary HTTP GET request to the user-provided target, with redirects enabled.

All HTTP response analysis must come from that request.

The scanner may inspect:

* final URL,
* status code,
* headers,
* response body,
* response size,
* redirect history,
* response time,
* cookies returned in the response,
* response encoding,
* response content type,
* visible HTML metadata.

The scanner must not perform additional endpoint requests.

It must not request:

```text
/robots.txt
/sitemap.xml
/wp-admin
/wp-login.php
/admin
/.env
/.git
```

It must not perform any discovery pattern.

TLS certificate inspection is allowed only for the target hostname because it is part of transport metadata.

---

# 6. Architectural Pipeline

Version 1.2 must follow this pipeline.

```text
Input
  ↓
URL Normalization
  ↓
Primary HTTP Request
  ↓
Raw Evidence Capture
  ↓
Evidence Normalization
  ↓
Evidence Categorization
  ↓
Observation Generation
  ↓
Finding Generation
  ↓
Risk Interpretation
  ↓
Report Rendering
```

Each stage must remain separate.

No stage should perform work owned by another stage.

For example, the HTTP request layer must not decide risk.

The report layer must not inspect raw HTML for CMS markers.

The risk layer must not fetch additional data.

---

# 7. Target v1.2 Logical Components

The following logical components define the Version 1.2 architecture.

They may initially exist as functions within existing files, but the implementation should make future modular extraction simple.

## 7.1 Input Handler

Owner:

```text
main.py
```

Responsibilities:

* parse CLI arguments,
* accept interactive input,
* handle `--version`,
* validate that a target was provided,
* pass the target into the scan workflow.

It must not:

* fetch websites,
* inspect headers,
* calculate risk,
* format full reports.

---

## 7.2 URL Utility Layer

Owner:

```text
utils.py
```

Responsibilities:

* normalize user-provided input,
* add default scheme when missing,
* extract hostname,
* remove path/query when hostname is needed,
* preserve original input,
* prepare safe request target.

Required functions:

```python
normalize_url(value: str) -> str
extract_hostname(value: str) -> str
```

Expected behaviour:

Input:

```text
example.com
```

Normalized URL:

```text
https://example.com
```

Hostname:

```text
example.com
```

Input:

```text
https://example.com/path?x=1
```

Normalized URL:

```text
https://example.com/path?x=1
```

Hostname:

```text
example.com
```

The URL utility layer must use standard library parsing where possible.

---

## 7.3 HTTP Fetch Layer

Owner:

```text
utils.py
```

Responsibilities:

* perform the primary HTTP GET request,
* apply timeout,
* allow redirects,
* capture response object details,
* return structured raw response evidence,
* return explicit failure data when request fails.

Required function:

```python
fetch_site(url: str) -> dict
```

Expected successful return shape:

```python
{
    "success": True,
    "requested_url": "https://example.com",
    "final_url": "https://www.example.com/",
    "status_code": 200,
    "headers": {},
    "content": "...",
    "size_bytes": 125000,
    "redirect_history": [],
    "error": None
}
```

Expected failed return shape:

```python
{
    "success": False,
    "requested_url": "https://example.com",
    "final_url": None,
    "status_code": None,
    "headers": {},
    "content": "",
    "size_bytes": 0,
    "redirect_history": [],
    "error": "Request failed or timed out"
}
```

The function must not return implicit `None`.

All failures must be explicit.

---

## 7.4 Connectivity Collector

Owner:

```text
scanner.py
```

Future owner:

```text
scanner/connectivity.py
```

Responsibilities:

* determine whether the site is reachable,
* measure response time,
* record status code,
* record final URL,
* record redirect count,
* preserve redirect history summary.

Expected output:

```python
{
    "reachable": True,
    "status_code": 200,
    "response_time_seconds": 1.24,
    "final_url": "https://www.example.com/",
    "redirect_count": 1,
    "redirect_chain": [
        {
            "status_code": 301,
            "url": "https://example.com"
        }
    ]
}
```

The connectivity collector must not decide whether missing headers are risky.

---

## 7.5 TLS Collector

Owner:

```text
scanner.py
```

Future owner:

```text
scanner/tls.py
```

Responsibilities:

* connect to the target hostname on port 443,
* retrieve certificate metadata,
* determine certificate validity,
* calculate days until expiry,
* return structured TLS evidence.

Allowed behaviour:

TLS inspection of the same target hostname.

Disallowed behaviour:

* scanning other ports,
* testing cipher suites,
* testing protocol downgrade paths,
* enumerating TLS configurations aggressively.

Expected successful output:

```python
{
    "checked": True,
    "valid": True,
    "days_until_expiry": 82,
    "not_after": "2026-09-20T12:00:00Z",
    "issuer": "Example CA",
    "subject": "example.com",
    "error": None
}
```

Expected failed output:

```python
{
    "checked": True,
    "valid": False,
    "days_until_expiry": None,
    "not_after": None,
    "issuer": None,
    "subject": None,
    "error": "TLS certificate could not be verified"
}
```

The TLS collector must catch specific expected exceptions.

Bare `except:` is not allowed.

---

## 7.6 Header Collector

Owner:

```text
scanner.py
```

Future owner:

```text
scanner/headers.py
```

Responsibilities:

* collect every response header returned by the HTTP response,
* preserve original names and values,
* normalize names for internal lookup,
* categorize known headers using the header knowledge base,
* place unknown headers into a vendor-specific or unclassified category,
* return structured header evidence.

Important rule:

Site Inspector must never discard a response header simply because it does not understand it.

Expected output:

```python
{
    "raw": {
        "Content-Type": "text/html; charset=UTF-8",
        "Cache-Control": "max-age=3600",
        "X-Custom-Edge": "edge-01"
    },
    "categorized": {
        "content_metadata": [],
        "caching_freshness": [],
        "vendor_specific_unclassified": []
    },
    "summary": {
        "total_headers": 3,
        "known_headers": 2,
        "unknown_headers": 1
    }
}
```

---

## 7.7 Header Knowledge Base

Owner:

```text
knowledge_base/headers.py
```

or initially:

```text
scanner.py
```

Preferred v1.2 target:

```text
knowledge_base/
    __init__.py
    headers.py
```

Responsibilities:

The header knowledge base defines what Site Inspector knows about headers.

It should be data-driven.

Each header entry should include:

```python
{
    "canonical_name": "Content-Security-Policy",
    "normalized_name": "content-security-policy",
    "category": "Security & Browser Protection",
    "purpose": "...",
    "expected": "present",
    "recommended_values": [],
    "deprecated": False,
    "risk_if_missing": "medium",
    "risk_if_present": None,
    "interpretation_present": "...",
    "interpretation_missing": "...",
    "recommendation_missing": "...",
    "references": []
}
```

The scanner should not hardcode interpretation rules if they can be represented in the knowledge base.

The knowledge base should be easy to expand.

Adding a known header should usually require adding one dictionary entry, not rewriting scanner logic.

---

## 7.8 Cookie Collector

Owner:

```text
scanner.py
```

Future owner:

```text
scanner/cookies.py
```

Responsibilities:

* detect whether `Set-Cookie` exists,
* parse cookie attributes where possible,
* detect `Secure`,
* detect `HttpOnly`,
* detect `SameSite`,
* detect `Path`,
* detect `Domain`,
* detect `Expires`,
* detect `Max-Age`,
* handle absence of cookies gracefully.

Expected output:

```python
{
    "present": True,
    "cookies": [
        {
            "name": "sessionid",
            "secure": True,
            "httponly": True,
            "samesite": "Lax",
            "path": "/",
            "domain": None,
            "expires": None,
            "max_age": None
        }
    ],
    "summary": {
        "total": 1,
        "secure_count": 1,
        "httponly_count": 1,
        "samesite_count": 1
    }
}
```

If no cookies are present:

```python
{
    "present": False,
    "cookies": [],
    "summary": {
        "total": 0,
        "secure_count": 0,
        "httponly_count": 0,
        "samesite_count": 0
    }
}
```

The absence of cookies must not automatically be treated as a problem.

---

## 7.9 Cache Collector

Owner:

```text
scanner.py
```

Future owner:

```text
scanner/cache.py
```

Responsibilities:

* inspect `Cache-Control`,
* inspect `Expires`,
* inspect `ETag`,
* inspect `Last-Modified`,
* inspect `Vary`,
* determine whether basic cache configuration is observable.

Expected output:

```python
{
    "cache_control": "max-age=3600",
    "expires": None,
    "etag": "\"abc123\"",
    "last_modified": "Mon, 01 Jan 2026 10:00:00 GMT",
    "vary": "Accept-Encoding",
    "configured": True
}
```

The cache collector should not assume every website requires the same caching strategy.

Interpretation belongs to the rule/finding layer.

---

## 7.10 Compression Collector

Owner:

```text
scanner.py
```

Future owner:

```text
scanner/compression.py
```

Responsibilities:

* inspect `Content-Encoding`,
* identify gzip,
* identify br,
* identify deflate,
* identify zstd if present,
* report whether compression is observable.

Expected output:

```python
{
    "enabled": True,
    "method": "br"
}
```

If absent:

```python
{
    "enabled": False,
    "method": None
}
```

Compression absence is usually a performance observation, not a high-risk issue.

---

## 7.11 Infrastructure Collector

Owner:

```text
scanner.py
```

Future owner:

```text
scanner/infrastructure.py
```

Responsibilities:

* extract observable infrastructure hints from headers,
* detect common CDN/proxy indicators,
* preserve server disclosure information,
* avoid overclaiming infrastructure identity.

Observable headers include:

```text
Server
X-Powered-By
Via
CF-Ray
CF-Cache-Status
X-Cache
X-Served-By
X-Backend-Server
X-Forwarded-Server
Alt-Svc
```

Expected output:

```python
{
    "server": "nginx",
    "x_powered_by": "PHP/8.2",
    "via": None,
    "cdn_indicators": [
        {
            "provider": "Cloudflare",
            "evidence": "CF-Ray header present"
        }
    ],
    "http3_hint": True
}
```

Infrastructure detection must use cautious language.

Example:

```text
Cloudflare indicators observed.
```

Avoid:

```text
This site uses Cloudflare.
```

Unless the evidence is strong and the wording remains conservative.

---

## 7.12 CMS Collector

Owner:

```text
scanner.py
```

Future owner:

```text
scanner/cms.py
```

Responsibilities:

* inspect the single returned HTML response,
* detect CMS indicators,
* return confidence level where possible,
* avoid extra requests.

Allowed CMS fingerprints from returned HTML:

```text
wp-content
wp-json
cdn.shopify.com
wixstatic.com
/sites/default/
/components/com_
```

Expected output:

```python
{
    "detected": True,
    "name": "WordPress",
    "confidence": "medium",
    "evidence": [
        "wp-content marker found in HTML"
    ]
}
```

If unknown:

```python
{
    "detected": False,
    "name": "Unknown",
    "confidence": "none",
    "evidence": []
}
```

CMS detection must never trigger admin checks or platform probing.

---

## 7.13 HTML Metadata Collector

Owner:

```text
scanner.py`
```

Future owner:

```text
scanner/html.py
```

Responsibilities:

* inspect already collected HTML content,
* extract basic metadata,
* avoid requiring external HTML parsing libraries unless approved.

Target metadata:

```text
<title>
meta description
canonical URL
viewport meta
charset
generator meta
script count
stylesheet count
```

Expected output:

```python
{
    "title": "Example Website",
    "meta_description_present": True,
    "canonical_present": True,
    "viewport_present": True,
    "charset": "UTF-8",
    "generator": "WordPress 6.x",
    "script_count": 12,
    "stylesheet_count": 4
}
```

HTML metadata is operational evidence.

It may support observations about maintainability, SEO readiness, and page structure.

It must not be used to make unsupported claims.

---

## 7.14 Page Weight Collector

Owner:

```text
scanner.py
```

Future owner:

```text
scanner/performance.py
```

Responsibilities:

* use already collected response payload size,
* classify page weight,
* support performance-related observations.

Suggested classification:

```text
Small: under 500 KB
Moderate: 500 KB to 2 MB
Large: above 2 MB
```

Expected output:

```python
{
    "size_bytes": 1250000,
    "size_kb": 1220.7,
    "classification": "Moderate"
}
```

The classification should be advisory.

It should not imply the website is poorly optimized without further evidence.

---

# 8. Evidence Model

Version 1.2 must introduce a formal evidence model.

Evidence represents raw or directly derived facts.

Evidence must be:

* traceable,
* structured,
* deterministic,
* machine-readable,
* reportable.

Generic evidence object:

```python
{
    "id": "header.content_security_policy",
    "category": "Security & Browser Protection",
    "source": "HTTP response header",
    "name": "Content-Security-Policy",
    "value": None,
    "present": False,
    "raw": None
}
```

Evidence must not contain recommendations.

Evidence must not contain subjective wording.

---

# 9. Observation Model

An observation is a factual statement derived from evidence.

Generic observation object:

```python
{
    "id": "observation.header.csp.missing",
    "evidence_id": "header.content_security_policy",
    "category": "Security & Browser Protection",
    "message": "The response does not include a Content-Security-Policy header."
}
```

Observations should remain factual.

They should not sound like warnings.

---

# 10. Finding Model

A finding combines evidence, observation, interpretation, recommendation, and optional risk contribution.

Generic finding object:

```python
{
    "id": "finding.header.csp.missing",
    "category": "Security & Browser Protection",
    "title": "Content-Security-Policy header not observed",
    "evidence": {
        "source": "HTTP response header",
        "header": "Content-Security-Policy",
        "observed_value": None
    },
    "observation": "The response does not include a Content-Security-Policy header.",
    "interpretation": "The browser is not receiving a site-defined policy for restricting permitted content sources.",
    "recommendation": "Consider defining a Content-Security-Policy appropriate to the application after testing it in report-only mode.",
    "risk_contribution": "Medium",
    "score": 2
}
```

Findings must remain grounded in evidence.

---

# 11. Recommendation Model

Recommendations should be practical and consultant-like.

They should avoid commands unless the issue is severe.

Preferred wording:

```text
Consider enabling...
Review whether...
Confirm that...
If this behaviour is intentional, no action may be required.
Configuration improvement recommended.
```

Avoid:

```text
Fix immediately.
Critical vulnerability.
Your site is unsafe.
Attackers can exploit this.
```

---

# 12. Risk Model

Risk is calculated from findings.

Risk must not be calculated from unstructured strings.

Target structure:

```python
{
    "level": "Medium",
    "score": 6,
    "summary": "The site is reachable and serving content, but several configuration improvements are recommended.",
    "contributors": [
        "finding.header.csp.missing",
        "finding.header.hsts.missing"
    ]
}
```

Risk levels:

```text
Low
Medium
High
```

Optional future levels:

```text
Informational
Critical
```

Do not introduce `Critical` in v1.2 unless explicitly approved.

---

# 13. Scan Result Model

Version 1.2 must move toward a single structured scan result object.

Target shape:

```python
{
    "project": {
        "name": "Site Inspector",
        "version": "v1.2"
    },
    "target": {
        "input": "example.com",
        "normalized_url": "https://example.com",
        "hostname": "example.com",
        "final_url": "https://www.example.com/"
    },
    "request": {
        "method": "GET",
        "timeout_seconds": 10,
        "redirects_enabled": True,
        "single_request_model": True
    },
    "connectivity": {},
    "tls": {},
    "response": {},
    "headers": {},
    "cookies": {},
    "cache": {},
    "compression": {},
    "infrastructure": {},
    "platform": {},
    "html": {},
    "performance": {},
    "evidence": [],
    "observations": [],
    "findings": [],
    "risk": {}
}
```

Codex should not necessarily implement every nested field in one pass, but all v1.2 code should move toward this shape.

---

# 14. Rule-Based Interpretation Model

Version 1.2 should adopt a rule-based interpretation model.

This means the tool should avoid scattering interpretation logic throughout scanner functions.

The scanner collects evidence.

The knowledge base classifies evidence.

The interpretation layer converts evidence into observations and findings.

Rules may initially be implemented as Python dictionaries and functions.

A full external rule engine is not required for v1.2.

Acceptable v1.2 implementation:

```text
knowledge_base/headers.py
risk.py
```

or:

```text
rules/headers.py
risk.py
```

Future target:

```text
rules/
    headers.py
    tls.py
    cookies.py
    cache.py
    performance.py
    cms.py
```

Each rule should be deterministic.

Each rule should produce structured findings.

---

# 15. Header Categorization Architecture

Every observed response header must be categorized.

Known headers should use the header knowledge base.

Unknown headers must be categorized as:

```text
Vendor-Specific / Unclassified
```

Required categories:

```text
Security & Browser Protection
Caching & Freshness
Compression & Transfer
Content Metadata
Cookies & Sessions
Redirect & Location
CORS & Cross-Origin Access
CDN / Proxy / Edge Infrastructure
Server / Application Disclosure
Protocol / Connection Behaviour
Legacy / Deprecated Headers
Vendor-Specific / Unclassified
```

The category name must be stable because report output and JSON output may depend on it.

---

# 16. Report Architecture

The report layer must be hierarchical.

The report should begin with a high-level summary and then allow users to inspect deeper technical detail.

Required order:

```text
1. Executive Summary
2. Target & Request
3. Connectivity
4. Transport Security
5. HTTP Response
6. Header Overview
7. Header Categories
8. Cookies & Sessions
9. Cache & Freshness
10. Compression & Transfer
11. Infrastructure Indicators
12. Platform Detection
13. HTML Metadata
14. Performance Indicators
15. Operational Findings
16. Recommendations
17. Raw Evidence
```

The console report does not need to print every raw header value twice, but every observed header must be visible somewhere, either in the categorized header section or raw evidence section.

---

# 17. JSON Output Architecture

Version 1.2 may introduce JSON output.

If implemented, JSON output must be generated from the same `scan_result` object as the console report.

CLI example:

```bash
python main.py --domain example.com --json
```

Rules:

* JSON must be machine-readable.
* JSON must include raw evidence.
* JSON must include categorized headers.
* JSON must include findings.
* JSON must include risk summary.
* JSON must not contain console formatting strings.

Console report and JSON report must not be built from separate scan logic.

---

# 18. Error Handling Architecture

Errors must be represented as structured evidence.

The program should not crash during normal failure conditions.

Normal failure conditions include:

* invalid domain,
* DNS failure,
* timeout,
* TLS verification failure,
* redirect failure,
* missing headers,
* empty response body,
* non-HTML response,
* missing certificate fields.

Error object pattern:

```python
{
    "component": "tls",
    "message": "TLS certificate could not be verified",
    "recoverable": True
}
```

Recoverable errors should appear in the report as operational observations where relevant.

---

# 19. Logging Policy

Version 1.2 does not require a logging subsystem.

Console output is sufficient.

If logging is added later, it must not replace structured evidence or reporting.

Logging should be for developer diagnostics, not primary user reporting.

---

# 20. Dependency Policy

Version 1.2 should avoid unnecessary dependencies.

Allowed:

```text
requests
standard library modules
```

Standard library modules likely needed:

```text
argparse
datetime
email.utils
html.parser
json
re
socket
ssl
time
urllib.parse
```

Avoid unless explicitly approved:

```text
BeautifulSoup
Selenium
Scrapy
httpx
nmap
security scanning libraries
web frameworks
```

---

# 21. Documentation Architecture

Every public function must include a docstring.

Docstrings should explain:

* what the function does,
* what input it expects,
* what output it returns,
* how failure is represented.

Good docstring pattern:

```python
def extract_hostname(value: str) -> str:
    """
    Extract a hostname from a user-provided URL or domain.

    Parameters
    ----------
    value:
        Domain or URL provided by the user.

    Returns
    -------
    str
        Hostname suitable for TLS inspection.

    Notes
    -----
    This function does not perform network activity.
    """
```

Inline comments should explain non-obvious reasoning.

Do not comment obvious statements.

Bad comment:

```python
# Loop over headers
for header in headers:
```

Good comment:

```python
# Unknown headers are preserved because they may indicate CDN,
# hosting, or application-specific behaviour not yet classified.
```

---

# 22. Testing Architecture

Version 1.2 should support manual and future automated testing.

Minimum manual tests:

```bash
python main.py --version
python main.py --domain example.com
python main.py
```

Required behaviours:

* version command exits without scanning,
* domain argument does not prompt,
* interactive mode prompts,
* unreachable site exits gracefully,
* TLS failure does not crash,
* missing headers do not crash,
* unknown headers are reported,
* compression method displays correctly,
* README version matches code version,
* report uses consultant-style language.

Future automated tests should target:

```text
URL normalization
hostname extraction
header categorization
cookie parsing
cache parsing
compression detection
CMS detection
risk scoring
report rendering
```

---

# 23. Backward Compatibility

Version 1.2 should preserve basic usage from Version 1.1.

Existing users should still be able to run:

```bash
python main.py
```

and:

```bash
python main.py --domain example.com
```

The output may become more detailed, but the core command-line experience must remain recognizable.

---

# 24. Prohibited Architectural Changes

Codex must not:

* merge all code into one file,
* move risk logic into scanner functions,
* move network logic into report functions,
* make additional HTTP requests for extra checks,
* convert the project into a web app,
* add asynchronous scanning,
* add crawling,
* add endpoint probing,
* replace deterministic rules with AI-generated interpretation,
* remove current functionality without explicit instruction.

---

# 25. v1.2 Implementation Priority

Codex should implement v1.2 in this order.

## Phase 1 — Correctness Cleanup

Fix current bugs and inconsistencies.

Required:

* explicit failure return from `fetch_site`,
* compression display bug,
* README version mismatch,
* bare `except` in TLS handling,
* risk wording tone,
* hostname extraction centralization.

## Phase 2 — Structured Scan Result

Introduce a structured result object without breaking the CLI.

## Phase 3 — Header Collection and Categorization

Collect all headers.

Categorize known headers.

Preserve unknown headers.

## Phase 4 — Header Knowledge Base

Move header definitions into a dedicated dictionary/module.

## Phase 5 — Findings Model

Generate structured findings from evidence.

## Phase 6 — Hierarchical Report

Replace flat report with layered professional output.

## Phase 7 — Optional JSON Output

Add JSON output only after the structured result is stable.

---

# 26. Success Criteria for Volume II

The architecture is successful if:

* Site Inspector remains passive,
* every layer has a clear responsibility,
* evidence is preserved before interpretation,
* all headers are collected and categorized,
* unknown headers are not discarded,
* findings are traceable to evidence,
* reports are hierarchical,
* risk scoring remains conservative,
* the project remains maintainable,
* future modules can be split without redesigning the whole system.

---

# 27. Final Architectural Rule

Site Inspector must always be designed as a configuration intelligence engine.

The HTTP request is only the evidence collection mechanism.

The product value lies in classification, interpretation, explanation, and professional reporting.
