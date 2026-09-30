# Site Inspector Technical Design Specification (TDS)

**Volume III — Data Models & Schemas**

**Document Version:** 1.0
**Project Version Covered:** Current v1.1 → Target v1.2
**Status:** Authoritative Engineering Specification
**Depends On:** Volume I — Project Constitution
**Depends On:** Volume II — System Architecture & Implementation Model

---

# 1. Purpose of this Volume

This volume defines the formal data models used by Site Inspector.

The purpose of this volume is to ensure that every stage of the system communicates through predictable, structured, deterministic objects.

Codex must treat these schemas as implementation contracts.

Where the current v1.1 implementation uses several separate dictionaries passed between functions, Version 1.2 must move toward one unified `ScanResult` object containing all collected evidence, derived observations, generated findings, recommendations, and risk summaries.

This document defines:

* the root scan result model,
* target model,
* request model,
* connectivity model,
* TLS model,
* response model,
* header model,
* cookie model,
* cache model,
* compression model,
* infrastructure model,
* platform model,
* HTML metadata model,
* performance model,
* evidence model,
* observation model,
* finding model,
* recommendation model,
* risk model,
* error model,
* and report model.

The schemas in this volume should guide both console reporting and future JSON output.

---

# 2. General Data Model Rules

All Site Inspector data structures must follow these rules.

Field names must use `snake_case`.

Boolean fields must use clear names such as:

```text
present
enabled
valid
reachable
configured
deprecated
```

Avoid vague names such as:

```text
ok
bad
flag
thing
result
```

Missing data should be represented with `None`, empty strings, empty lists, or explicit error objects depending on context.

A function should not return implicit `None` for expected operational failures.

Data should be structured before it is rendered.

Console formatting should happen only in the report layer.

Risk wording should not appear in raw evidence objects.

Evidence objects should remain factual.

Findings may include interpretation and recommendations.

---

# 3. Canonical Root Object: `ScanResult`

The `ScanResult` object is the authoritative output of the scan workflow.

All report output should eventually be rendered from this object.

Target structure:

```python
scan_result = {
    "project": {},
    "target": {},
    "request": {},
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
    "recommendations": [],
    "risk": {},
    "errors": []
}
```

Every top-level key must exist, even if the value is empty or unavailable.

This ensures stable JSON output and predictable report rendering.

---

# 4. `ProjectInfo` Model

The `project` section identifies the tool and version that produced the result.

Schema:

```python
{
    "name": "Site Inspector",
    "version": "v1.2",
    "description": "Passive Website Configuration Auditor"
}
```

Required fields:

```text
name
version
description
```

Rules:

The version must match the constant defined in the application entry point.

The README version must match this value.

---

# 5. `TargetInfo` Model

The `target` section describes the user-provided website target.

Schema:

```python
{
    "input": "example.com",
    "normalized_url": "https://example.com",
    "hostname": "example.com",
    "final_url": "https://www.example.com/"
}
```

Required fields:

```text
input
normalized_url
hostname
final_url
```

Field meanings:

`input` is the original value provided by the user.

`normalized_url` is the URL prepared for the HTTP request.

`hostname` is the hostname used for TLS inspection.

`final_url` is the final URL after redirects.

If the request fails, `final_url` may be `None`.

Example failed target:

```python
{
    "input": "bad-example.invalid",
    "normalized_url": "https://bad-example.invalid",
    "hostname": "bad-example.invalid",
    "final_url": None
}
```

---

# 6. `RequestInfo` Model

The `request` section records how Site Inspector collected primary evidence.

Schema:

```python
{
    "method": "GET",
    "timeout_seconds": 10,
    "redirects_enabled": True,
    "single_request_model": True,
    "user_agent": None
}
```

Required fields:

```text
method
timeout_seconds
redirects_enabled
single_request_model
user_agent
```

Rules:

`method` must be `GET` for v1.2.

`single_request_model` must be `True`.

If a custom user agent is not used, `user_agent` should be `None`.

The request section should make clear that evidence was collected from a standard page request.

---

# 7. `ConnectivityResult` Model

The `connectivity` section describes reachability and HTTP response behaviour.

Schema:

```python
{
    "reachable": True,
    "status_code": 200,
    "response_time_seconds": 1.24,
    "redirect_count": 1,
    "redirect_chain": [
        {
            "status_code": 301,
            "url": "https://example.com",
            "location": "https://www.example.com/"
        }
    ]
}
```

Required fields:

```text
reachable
status_code
response_time_seconds
redirect_count
redirect_chain
```

Failed example:

```python
{
    "reachable": False,
    "status_code": None,
    "response_time_seconds": None,
    "redirect_count": 0,
    "redirect_chain": []
}
```

Rules:

Response time should be rounded to two decimal places.

Redirect chain should preserve observable redirect history from the primary request.

No additional redirect probing is allowed.

---

# 8. `TLSResult` Model

The `tls` section describes certificate evidence for the target hostname.

Schema:

```python
{
    "checked": True,
    "valid": True,
    "days_until_expiry": 82,
    "not_before": "2026-06-01T00:00:00Z",
    "not_after": "2026-09-20T12:00:00Z",
    "issuer": "Example Certificate Authority",
    "subject": "example.com",
    "serial_number": None,
    "error": None
}
```

Required fields:

```text
checked
valid
days_until_expiry
not_before
not_after
issuer
subject
serial_number
error
```

Failed example:

```python
{
    "checked": True,
    "valid": False,
    "days_until_expiry": None,
    "not_before": None,
    "not_after": None,
    "issuer": None,
    "subject": None,
    "serial_number": None,
    "error": "TLS certificate could not be verified"
}
```

Rules:

TLS errors should not crash the program.

The TLS collector must catch specific exceptions.

Bare exception handling is forbidden.

A failed TLS check may contribute to risk, but the evidence model itself must remain factual.

---

# 9. `HTTPResponseInfo` Model

The `response` section describes the final HTTP response.

Schema:

```python
{
    "status_code": 200,
    "content_type": "text/html; charset=UTF-8",
    "content_length": "125000",
    "size_bytes": 125000,
    "encoding": "gzip",
    "body_present": True,
    "body_sample": None
}
```

Required fields:

```text
status_code
content_type
content_length
size_bytes
encoding
body_present
body_sample
```

Rules:

`body_sample` should remain `None` in v1.2 unless explicitly required.

Do not print full HTML in the default console report.

The raw HTML may be used internally for CMS and metadata detection.

---

# 10. `HeadersResult` Model

The `headers` section is one of the most important parts of v1.2.

It must preserve every response header.

Schema:

```python
{
    "raw": {},
    "normalized": {},
    "categorized": {},
    "summary": {}
}
```

---

## 10.1 Raw Headers

Raw headers preserve observed names and values.

Example:

```python
{
    "Content-Type": "text/html; charset=UTF-8",
    "Cache-Control": "max-age=3600",
    "X-Custom-Edge": "edge-01"
}
```

Rules:

Raw header names should be preserved as returned by the HTTP library.

Do not discard unknown headers.

---

## 10.2 Normalized Headers

Normalized headers support case-insensitive lookup.

Example:

```python
{
    "content-type": {
        "original_name": "Content-Type",
        "value": "text/html; charset=UTF-8"
    },
    "cache-control": {
        "original_name": "Cache-Control",
        "value": "max-age=3600"
    }
}
```

Rules:

Normalized names must be lowercase.

Original casing must still be preserved.

---

## 10.3 Categorized Headers

Every header must appear in exactly one primary category.

Schema:

```python
{
    "security_browser_protection": [],
    "caching_freshness": [],
    "compression_transfer": [],
    "content_metadata": [],
    "cookies_sessions": [],
    "redirect_location": [],
    "cors_cross_origin_access": [],
    "cdn_proxy_edge_infrastructure": [],
    "server_application_disclosure": [],
    "protocol_connection_behaviour": [],
    "legacy_deprecated": [],
    "vendor_specific_unclassified": []
}
```

Each categorized header entry:

```python
{
    "name": "Content-Security-Policy",
    "normalized_name": "content-security-policy",
    "value": None,
    "present": False,
    "known": True,
    "category": "Security & Browser Protection",
    "deprecated": False,
    "purpose": "Defines browser-enforced restrictions for permitted content sources.",
    "interpretation": "The response does not include a site-defined content policy.",
    "recommendation": "Consider defining a Content-Security-Policy appropriate to the application after testing.",
    "risk_contribution": "Medium"
}
```

For unknown headers:

```python
{
    "name": "X-Custom-Edge",
    "normalized_name": "x-custom-edge",
    "value": "edge-01",
    "present": True,
    "known": False,
    "category": "Vendor-Specific / Unclassified",
    "deprecated": False,
    "purpose": None,
    "interpretation": "Header observed but not classified by Site Inspector.",
    "recommendation": None,
    "risk_contribution": "Informational"
}
```

Rules:

Known but missing headers may appear in their category if they are part of the knowledge base and expected to be checked.

Observed unknown headers must always appear in `vendor_specific_unclassified`.

Observed known headers must appear in their correct category.

---

## 10.4 Header Summary

Schema:

```python
{
    "total_observed": 12,
    "known_observed": 9,
    "unknown_observed": 3,
    "expected_known_missing": 4,
    "deprecated_observed": 1
}
```

Rules:

The summary should separate observed headers from expected-but-missing known headers.

---

# 11. `CookieResult` Model

The `cookies` section describes cookie evidence from `Set-Cookie`.

Schema:

```python
{
    "present": True,
    "cookies": [],
    "summary": {}
}
```

Cookie entry:

```python
{
    "name": "sessionid",
    "secure": True,
    "httponly": True,
    "samesite": "Lax",
    "path": "/",
    "domain": None,
    "expires": None,
    "max_age": None,
    "raw": "sessionid=abc; Secure; HttpOnly; SameSite=Lax; Path=/"
}
```

Summary:

```python
{
    "total": 1,
    "secure_count": 1,
    "httponly_count": 1,
    "samesite_count": 1,
    "missing_secure_count": 0,
    "missing_httponly_count": 0,
    "missing_samesite_count": 0
}
```

No-cookie example:

```python
{
    "present": False,
    "cookies": [],
    "summary": {
        "total": 0,
        "secure_count": 0,
        "httponly_count": 0,
        "samesite_count": 0,
        "missing_secure_count": 0,
        "missing_httponly_count": 0,
        "missing_samesite_count": 0
    }
}
```

Rules:

The absence of cookies is not automatically a problem.

Cookie risk should only be generated when cookies are present and relevant attributes are missing.

---

# 12. `CacheResult` Model

The `cache` section describes freshness and caching evidence.

Schema:

```python
{
    "cache_control": "max-age=3600",
    "expires": None,
    "etag": "\"abc123\"",
    "last_modified": "Mon, 01 Jan 2026 10:00:00 GMT",
    "vary": "Accept-Encoding",
    "configured": True,
    "directives": {
        "max_age": 3600,
        "no_cache": False,
        "no_store": False,
        "public": False,
        "private": False,
        "must_revalidate": False
    }
}
```

Required fields:

```text
cache_control
expires
etag
last_modified
vary
configured
directives
```

Rules:

Cache interpretation must be conservative.

Different websites have different cache requirements.

Absence of caching is usually a performance or efficiency observation, not a severe operational issue.

---

# 13. `CompressionResult` Model

The `compression` section describes compression evidence.

Schema:

```python
{
    "enabled": True,
    "method": "br",
    "content_encoding": "br"
}
```

Absent example:

```python
{
    "enabled": False,
    "method": None,
    "content_encoding": None
}
```

Rules:

Recognized compression methods:

```text
gzip
br
deflate
zstd
```

Unknown methods should be preserved as observed.

---

# 14. `InfrastructureResult` Model

The `infrastructure` section describes publicly observable infrastructure hints.

Schema:

```python
{
    "server": "nginx",
    "x_powered_by": "PHP/8.2",
    "via": None,
    "cdn_indicators": [],
    "proxy_indicators": [],
    "edge_indicators": [],
    "http3_hint": False,
    "raw_headers_used": []
}
```

CDN indicator example:

```python
{
    "provider": "Cloudflare",
    "evidence": "CF-Ray header observed",
    "confidence": "high"
}
```

Rules:

Infrastructure output should use cautious wording.

The tool may say:

```text
Cloudflare indicators observed.
```

It should avoid overclaiming:

```text
This website definitely uses Cloudflare for all traffic.
```

---

# 15. `PlatformResult` Model

The `platform` section describes CMS or platform detection.

Schema:

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

Unknown example:

```python
{
    "detected": False,
    "name": "Unknown",
    "confidence": "none",
    "evidence": []
}
```

Allowed confidence values:

```text
none
low
medium
high
```

Rules:

CMS detection must rely only on the single returned HTML response.

Do not perform CMS-specific endpoint checks.

CMS detection should usually be informational.

---

# 16. `HTMLMetadataResult` Model

The `html` section describes metadata extracted from the returned HTML content.

Schema:

```python
{
    "title": "Example Website",
    "title_present": True,
    "meta_description_present": True,
    "meta_description": "Example description.",
    "canonical_present": True,
    "canonical_url": "https://www.example.com/",
    "viewport_present": True,
    "charset": "UTF-8",
    "generator": "WordPress 6.x",
    "script_count": 12,
    "stylesheet_count": 4
}
```

Required fields:

```text
title
title_present
meta_description_present
meta_description
canonical_present
canonical_url
viewport_present
charset
generator
script_count
stylesheet_count
```

Rules:

Do not require BeautifulSoup for v1.2 unless explicitly approved.

Use standard library or simple regex carefully.

HTML metadata extraction must not fetch additional resources.

Script and stylesheet counts should count references visible in the returned HTML only.

---

# 17. `PerformanceResult` Model

The `performance` section describes basic performance-related evidence available from the single response.

Schema:

```python
{
    "response_time_seconds": 1.24,
    "size_bytes": 1250000,
    "size_kb": 1220.7,
    "page_weight_classification": "Moderate",
    "compression_enabled": True,
    "cache_configured": True
}
```

Allowed page weight classifications:

```text
Small
Moderate
Large
Unknown
```

Suggested thresholds:

```text
Small: < 500 KB
Moderate: 500 KB to 2 MB
Large: > 2 MB
Unknown: unavailable
```

Rules:

Performance interpretation must be advisory because a single request is not a full performance test.

---

# 18. `Evidence` Model

Evidence objects represent objective facts.

Schema:

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

Required fields:

```text
id
category
source
name
value
present
raw
```

Rules:

Evidence must not include recommendations.

Evidence must not include subjective interpretation.

Evidence IDs must be stable and predictable.

Recommended ID pattern:

```text
header.<normalized_header_name>
tls.certificate_validity
connectivity.status_code
cookie.<cookie_name>.<attribute>
cache.cache_control
compression.content_encoding
platform.cms_detection
html.title
performance.page_weight
```

---

# 19. `Observation` Model

Observations are factual statements derived from evidence.

Schema:

```python
{
    "id": "observation.header.csp.missing",
    "evidence_id": "header.content_security_policy",
    "category": "Security & Browser Protection",
    "message": "The response does not include a Content-Security-Policy header."
}
```

Required fields:

```text
id
evidence_id
category
message
```

Rules:

Observation wording must remain factual.

Avoid alarmist phrasing.

Observation must not include unsupported speculation.

---

# 20. `Finding` Model

Findings combine evidence, observation, interpretation, recommendation, and optional risk contribution.

Schema:

```python
{
    "id": "finding.header.csp.missing",
    "category": "Security & Browser Protection",
    "title": "Content-Security-Policy header not observed",
    "evidence_ids": [
        "header.content_security_policy"
    ],
    "observation": "The response does not include a Content-Security-Policy header.",
    "interpretation": "The browser is not receiving a site-defined policy for restricting permitted content sources.",
    "recommendation": "Consider defining a Content-Security-Policy appropriate to the application after testing it in report-only mode.",
    "risk_contribution": "Medium",
    "score": 2
}
```

Required fields:

```text
id
category
title
evidence_ids
observation
interpretation
recommendation
risk_contribution
score
```

Allowed risk contribution values:

```text
Informational
Low
Medium
High
```

Rules:

Findings must be traceable to evidence.

High findings require strong evidence.

Do not create high findings for minor header omissions.

---

# 21. `Recommendation` Model

Recommendations may be stored separately for summary output.

Schema:

```python
{
    "id": "recommendation.header.csp.enable",
    "finding_id": "finding.header.csp.missing",
    "priority": "Medium",
    "message": "Consider defining a Content-Security-Policy appropriate to the application after testing it in report-only mode."
}
```

Required fields:

```text
id
finding_id
priority
message
```

Allowed priorities:

```text
Informational
Low
Medium
High
```

Rules:

Recommendations should be concise and actionable.

They should not overstate certainty.

---

# 22. `RiskSummary` Model

The `risk` section summarizes operational risk.

Schema:

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

Required fields:

```text
level
score
summary
contributors
```

Allowed levels:

```text
Low
Medium
High
```

Risk thresholds for v1.2:

```text
Low: 0–4
Medium: 5–8
High: 9+
```

High should remain conservative.

Invalid TLS, unreachable site, or TLS expiry soon may justify High depending on score.

---

# 23. `ErrorObject` Model

Errors should be structured and recoverable where possible.

Schema:

```python
{
    "component": "tls",
    "message": "TLS certificate could not be verified",
    "recoverable": True,
    "exception_type": "SSLError"
}
```

Required fields:

```text
component
message
recoverable
exception_type
```

Rules:

Errors must not expose unnecessary stack traces in normal console output.

Developer debugging may include more detail later.

---

# 24. `ReportSection` Model

The report may internally use section objects before printing.

Schema:

```python
{
    "title": "Transport Security",
    "summary": "TLS certificate is valid and expires in 82 days.",
    "items": [
        {
            "label": "TLS Valid",
            "value": "Yes"
        }
    ]
}
```

Required fields:

```text
title
summary
items
```

Rules:

Report sections are presentation objects.

They should be generated from `ScanResult`.

They should not collect evidence.

---

# 25. Complete Example `ScanResult`

Example successful result:

```python
{
    "project": {
        "name": "Site Inspector",
        "version": "v1.2",
        "description": "Passive Website Configuration Auditor"
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
        "single_request_model": True,
        "user_agent": None
    },
    "connectivity": {
        "reachable": True,
        "status_code": 200,
        "response_time_seconds": 1.24,
        "redirect_count": 1,
        "redirect_chain": []
    },
    "tls": {
        "checked": True,
        "valid": True,
        "days_until_expiry": 82,
        "not_before": None,
        "not_after": "2026-09-20T12:00:00Z",
        "issuer": "Example CA",
        "subject": "example.com",
        "serial_number": None,
        "error": None
    },
    "response": {
        "status_code": 200,
        "content_type": "text/html; charset=UTF-8",
        "content_length": "125000",
        "size_bytes": 125000,
        "encoding": "br",
        "body_present": True,
        "body_sample": None
    },
    "headers": {
        "raw": {},
        "normalized": {},
        "categorized": {},
        "summary": {}
    },
    "cookies": {
        "present": False,
        "cookies": [],
        "summary": {}
    },
    "cache": {
        "cache_control": "max-age=3600",
        "expires": None,
        "etag": None,
        "last_modified": None,
        "vary": "Accept-Encoding",
        "configured": True,
        "directives": {}
    },
    "compression": {
        "enabled": True,
        "method": "br",
        "content_encoding": "br"
    },
    "infrastructure": {
        "server": "nginx",
        "x_powered_by": None,
        "via": None,
        "cdn_indicators": [],
        "proxy_indicators": [],
        "edge_indicators": [],
        "http3_hint": False,
        "raw_headers_used": []
    },
    "platform": {
        "detected": False,
        "name": "Unknown",
        "confidence": "none",
        "evidence": []
    },
    "html": {
        "title": "Example Website",
        "title_present": True,
        "meta_description_present": True,
        "meta_description": "Example description.",
        "canonical_present": True,
        "canonical_url": "https://www.example.com/",
        "viewport_present": True,
        "charset": "UTF-8",
        "generator": None,
        "script_count": 4,
        "stylesheet_count": 2
    },
    "performance": {
        "response_time_seconds": 1.24,
        "size_bytes": 125000,
        "size_kb": 122.1,
        "page_weight_classification": "Small",
        "compression_enabled": True,
        "cache_configured": True
    },
    "evidence": [],
    "observations": [],
    "findings": [],
    "recommendations": [],
    "risk": {
        "level": "Low",
        "score": 2,
        "summary": "The site is reachable and serving content. Only minor configuration improvements were observed.",
        "contributors": []
    },
    "errors": []
}
```

---

# 26. Failed Scan Example

Example failed result:

```python
{
    "project": {
        "name": "Site Inspector",
        "version": "v1.2",
        "description": "Passive Website Configuration Auditor"
    },
    "target": {
        "input": "bad-example.invalid",
        "normalized_url": "https://bad-example.invalid",
        "hostname": "bad-example.invalid",
        "final_url": None
    },
    "request": {
        "method": "GET",
        "timeout_seconds": 10,
        "redirects_enabled": True,
        "single_request_model": True,
        "user_agent": None
    },
    "connectivity": {
        "reachable": False,
        "status_code": None,
        "response_time_seconds": None,
        "redirect_count": 0,
        "redirect_chain": []
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
        "error": "TLS check skipped because the site was unreachable"
    },
    "response": {
        "status_code": None,
        "content_type": None,
        "content_length": None,
        "size_bytes": 0,
        "encoding": None,
        "body_present": False,
        "body_sample": None
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
            "deprecated_observed": 0
        }
    },
    "cookies": {
        "present": False,
        "cookies": [],
        "summary": {}
    },
    "cache": {},
    "compression": {},
    "infrastructure": {},
    "platform": {},
    "html": {},
    "performance": {},
    "evidence": [],
    "observations": [],
    "findings": [
        {
            "id": "finding.connectivity.unreachable",
            "category": "Connectivity",
            "title": "Website unreachable",
            "evidence_ids": [
                "connectivity.reachable"
            ],
            "observation": "The website could not be reached during the request.",
            "interpretation": "The site did not return a usable HTTP response during the inspection.",
            "recommendation": "Confirm DNS, hosting availability, firewall rules, and server health.",
            "risk_contribution": "High",
            "score": 4
        }
    ],
    "recommendations": [],
    "risk": {
        "level": "High",
        "score": 4,
        "summary": "The site could not be reached, so configuration analysis could not be completed.",
        "contributors": [
            "finding.connectivity.unreachable"
        ]
    },
    "errors": [
        {
            "component": "http",
            "message": "Request failed or timed out",
            "recoverable": True,
            "exception_type": "RequestException"
        }
    ]
}
```

Note:

Although the unreachable finding has a score of 4, the risk level may be elevated to High by explicit rule because site unreachability is a critical operational condition. This exception must be documented in the risk rules.

---

# 27. Schema Stability Rules

Once implemented, field names should not change casually.

If a field must be renamed, the change should be treated as a breaking change and documented.

Optional fields may be added in minor versions.

Existing fields should not be removed without a versioned migration.

---

# 28. Implementation Guidance for Codex

Codex should not attempt to implement every schema perfectly in one pass if doing so would require a full rewrite.

Instead, Codex should migrate incrementally.

Recommended implementation order:

1. Create helper functions that return schema-compatible objects.
2. Preserve the existing CLI.
3. Build the `ScanResult` object in `main.py` or a new orchestration function.
4. Move interpretation toward findings.
5. Update `report.py` to render from structured data.
6. Add JSON output only after schema stability.

The final goal is not merely to make the code run.

The final goal is to make the code conform to a stable, extensible data contract.

---

# 29. Success Criteria for Volume III

The data model is successful if:

* every major output has a predictable place,
* raw evidence remains separate from interpretation,
* findings are traceable to evidence,
* headers are fully preserved,
* unknown headers are not lost,
* report output can be generated from the scan result,
* JSON output can eventually be generated without new scan logic,
* future modules can add data without breaking the whole structure,
* Codex can implement features without inventing new incompatible dictionaries.

---

# 30. Final Schema Rule

When in doubt, preserve the evidence.

It is better for Site Inspector to store more structured evidence than to discard information prematurely.

Interpretation can improve over time.

Lost evidence cannot be recovered after the scan.
