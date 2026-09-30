# Site Inspector Technical Design Specification (TDS)

**Volume V — Rule Engine, Findings & Risk Interpretation**

**Document Version:** 1.0
**Project Version Covered:** Target v1.2
**Status:** Authoritative Engineering Specification
**Depends On:** Volume I — Project Constitution
**Depends On:** Volume II — System Architecture & Implementation Model
**Depends On:** Volume III — Data Models & Schemas
**Depends On:** Volume IV — Header Knowledge Base

---

# 1. Purpose of this Volume

This volume defines how Site Inspector converts collected evidence into observations, findings, recommendations, and operational risk.

Volumes I through IV establish the project philosophy, system architecture, data contracts, and header knowledge base. This volume defines the interpretation engine that connects those pieces.

The rule engine must remain deterministic, conservative, evidence-based, and consultant-like.

It must never behave like an exploit scanner.

It must never generate findings that cannot be traced back to evidence.

---

# 2. Core Interpretation Principle

Site Inspector must not begin with risk.

It must begin with evidence.

The required interpretation chain is:

```text
Evidence
    ↓
Observation
    ↓
Finding
    ↓
Recommendation
    ↓
Risk Summary
```

Each layer adds meaning, but each layer must remain traceable to the layer before it.

A finding without evidence is invalid.

A recommendation without a finding is invalid unless explicitly marked as a general informational note.

A risk score without findings is invalid unless it represents a special operational condition such as site unreachability.

---

# 3. Rule Engine Responsibility

The rule engine is responsible for converting structured scan data into structured findings.

It must not collect evidence.

It must not make HTTP requests.

It must not parse command-line arguments.

It must not render console output.

Its inputs are structured objects such as:

```text
scan_result
headers
cookies
tls
connectivity
cache
compression
platform
html
performance
```

Its outputs are:

```text
observations
findings
recommendations
risk_summary
```

---

# 4. Recommended File Structure

For v1.2, the rule engine may remain partially inside `risk.py` if necessary, but the preferred structure is:

```text
rules/
    __init__.py
    headers.py
    tls.py
    connectivity.py
    cookies.py
    cache.py
    compression.py
    performance.py
    platform.py
    html.py
    combinations.py
```

The current `risk.py` may remain as the risk aggregation layer.

Preferred final structure:

```text
risk.py
rules/
knowledge_base/
```

Where:

```text
knowledge_base/
```

defines known facts and interpretation templates.

```text
rules/
```

applies those definitions to actual scan evidence.

```text
risk.py
```

aggregates findings into an overall operational risk summary.

---

# 5. Rule Object Model

Each rule should be deterministic and structured.

Recommended rule shape:

```python
{
    "id": "rule.header.csp.missing",
    "category": "Security & Browser Protection",
    "applies_to": "headers",
    "condition": "header_missing",
    "target": "content-security-policy",
    "finding_id": "finding.header.csp.missing",
    "title": "Content-Security-Policy header not observed",
    "observation_template": "The response does not include a Content-Security-Policy header.",
    "interpretation_template": "The browser is not receiving a site-defined policy for restricting permitted content sources.",
    "recommendation_template": "Consider defining a Content-Security-Policy appropriate to the application after testing it in report-only mode.",
    "risk_contribution": "Medium",
    "score": 2
}
```

Rules may be implemented as Python dictionaries or functions.

A full external rule engine is not required for v1.2.

The important requirement is that rule behaviour must be explicit and testable.

---

# 6. Rule Function Contract

Each rule function should accept structured scan data and return a list of findings or observations.

Example function contract:

```python
def evaluate_header_rules(scan_result: dict) -> list[dict]:
    """
    Evaluate header evidence and return structured findings.

    Parameters
    ----------
    scan_result:
        Complete structured scan result.

    Returns
    -------
    list[dict]
        Finding objects generated from header evidence.
    """
```

Rules must not mutate unrelated sections of `scan_result`.

Preferred pattern:

```python
findings = []
findings.extend(evaluate_connectivity_rules(scan_result))
findings.extend(evaluate_tls_rules(scan_result))
findings.extend(evaluate_header_rules(scan_result))
findings.extend(evaluate_cookie_rules(scan_result))
findings.extend(evaluate_cache_rules(scan_result))
findings.extend(evaluate_compression_rules(scan_result))
findings.extend(evaluate_performance_rules(scan_result))
findings.extend(evaluate_combination_rules(scan_result))
```

Then:

```python
risk = calculate_risk(findings, scan_result)
```

---

# 7. Observation Generation Rules

Observations are factual.

They must describe what was observed or not observed.

They must not exaggerate.

They must not include remediation instructions.

Good observation:

```text
The response does not include a Content-Security-Policy header.
```

Bad observation:

```text
The site is vulnerable because CSP is missing.
```

Good observation:

```text
The response sets a cookie without the Secure attribute.
```

Bad observation:

```text
The cookie can be stolen.
```

Observation wording must be restrained.

---

# 8. Finding Generation Rules

A finding should be generated when evidence has meaningful operational significance.

Findings may be generated for:

```text
site unreachable
invalid TLS
TLS expiring soon
slow response time
excessive redirects
missing important browser protection headers
important header present with unexpected value
deprecated header present
cookie missing important attributes
cache configuration absent
compression absent for text content
large page weight
broad CORS with credentials
server or application disclosure
CMS detected
HTML metadata missing
```

Findings should not be generated for every single observed fact.

Facts should still appear as evidence.

Findings are reserved for items that deserve explanation or review.

---

# 9. Recommendation Generation Rules

Recommendations must be practical, conservative, and conditional where appropriate.

Preferred phrases:

```text
Consider...
Review whether...
Confirm that...
If this behaviour is intentional, no action may be required.
Configuration improvement recommended.
Maintenance review recommended.
```

Avoid:

```text
Fix immediately.
Critical vulnerability.
Attackers can exploit this.
Your site is unsafe.
This is dangerous.
```

Recommendations should be written like a consultant advising a client.

---

# 10. Risk Contribution Values

Each finding may contribute to risk.

Allowed values:

```text
Informational
Low
Medium
High
```

Numeric scores:

```text
Informational: 0
Low: 1
Medium: 2
High: 3
```

Special operational overrides may apply for site unreachability and invalid TLS.

---

# 11. Overall Risk Levels

Overall operational risk levels:

```text
Low
Medium
High
```

Suggested score thresholds:

```text
Low: 0–4
Medium: 5–8
High: 9+
```

However, the risk engine may apply explicit overrides where operational impact is clear.

Overrides are defined later in this volume.

---

# 12. High Risk Rules

High risk must remain rare and defensible.

High risk may be assigned when:

```text
The site is unreachable.
TLS certificate is invalid or cannot be verified.
TLS certificate expires in fewer than 30 days.
The final response indicates serious server error conditions.
Multiple medium findings combine into a clear operational maintenance concern.
```

High risk must not be assigned merely because:

```text
Referrer-Policy is missing.
Permissions-Policy is missing.
Server header is present.
X-Powered-By is present.
CMS is detected.
Compression is absent.
Unknown headers exist.
```

---

# 13. Medium Risk Rules

Medium risk may be assigned when:

```text
Major browser protection headers are missing.
A cookie appears to lack Secure or HttpOnly.
Response time exceeds acceptable threshold.
Redirect behaviour appears inefficient.
Cache configuration is absent.
Content-Type is missing.
Broad CORS with credentials is observed.
```

Medium risk means:

```text
Configuration review recommended.
```

It does not mean:

```text
Compromise likely.
```

---

# 14. Low Risk Rules

Low risk applies to minor configuration improvements or low-impact disclosure.

Examples:

```text
Referrer-Policy missing.
Permissions-Policy missing.
Server header present.
X-Powered-By header present.
Compression not observed.
Cache validators absent.
HTML metadata incomplete.
CMS detected.
```

Low risk means:

```text
Optional or minor improvement recommended.
```

---

# 15. Informational Rules

Informational findings should not affect the score.

Examples:

```text
Cloudflare indicators observed.
Alt-Svc observed.
ETag observed.
Vary observed.
CSP Report-Only observed.
No cookies observed.
Unknown vendor header observed.
CMS unknown.
```

Informational findings explain the environment.

They are not risk concerns.

---

# 16. Connectivity Rules

## 16.1 Site Unreachable

Condition:

```text
connectivity.reachable is False
```

Finding:

```python
{
    "id": "finding.connectivity.unreachable",
    "category": "Connectivity",
    "title": "Website unreachable",
    "evidence_ids": ["connectivity.reachable"],
    "observation": "The website could not be reached during the request.",
    "interpretation": "The site did not return a usable HTTP response during the inspection.",
    "recommendation": "Confirm DNS, hosting availability, firewall rules, and server health.",
    "risk_contribution": "High",
    "score": 3
}
```

Overall risk override:

```text
High
```

Reason:

A site that cannot be reached has clear operational impact.

---

## 16.2 Server Error Status

Condition:

```text
status_code >= 500
```

Finding:

```text
Server error response observed
```

Risk:

```text
High
```

Score:

```text
3
```

Recommendation:

```text
Review server logs, application health, and upstream dependencies.
```

Notes:

A 5xx response from the homepage is an operational issue.

---

## 16.3 Client Error Status

Condition:

```text
status_code >= 400 and status_code < 500
```

Risk:

```text
Medium
```

Score:

```text
2
```

Recommendation:

```text
Confirm whether the homepage is intended to return this status code.
```

Notes:

Some 403 responses may be intentional. Use cautious wording.

---

## 16.4 Slow Response Time

Condition:

```text
response_time_seconds > 2.0
```

Risk:

```text
Medium
```

Score:

```text
2
```

Observation:

```text
The response took more than two seconds to complete.
```

Interpretation:

```text
Slow initial response may affect user experience, especially on slower networks.
```

Recommendation:

```text
Review hosting performance, backend processing time, caching, and CDN behaviour.
```

Notes:

Do not call this a full performance audit.

---

## 16.5 Very Slow Response Time

Condition:

```text
response_time_seconds > 5.0
```

Risk:

```text
High
```

Score:

```text
3
```

Recommendation:

```text
Review server health, backend latency, caching, and hosting resource constraints.
```

Notes:

Very slow homepage response can have meaningful operational impact.

---

## 16.6 Redirect Count Review

Condition:

```text
redirect_count >= 3
```

Risk:

```text
Low
```

Score:

```text
1
```

Recommendation:

```text
Review redirect chain to reduce unnecessary hops where practical.
```

---

## 16.7 Excessive Redirects

Condition:

```text
redirect_count > 5
```

Risk:

```text
Medium
```

Score:

```text
2
```

Recommendation:

```text
Review canonical URL, HTTPS enforcement, and www/non-www redirect configuration.
```

---

# 17. TLS Rules

## 17.1 TLS Invalid

Condition:

```text
tls.checked is True
tls.valid is False
```

Risk:

```text
High
```

Score:

```text
3
```

Overall risk override:

```text
High
```

Recommendation:

```text
Review certificate installation, hostname coverage, certificate chain, and expiry status.
```

Notes:

TLS failure has clear visitor trust and availability implications.

---

## 17.2 TLS Expiring Soon

Condition:

```text
tls.valid is True
days_until_expiry < 30
```

Risk:

```text
High
```

Score:

```text
3
```

Overall risk override:

```text
High
```

Recommendation:

```text
Renew or replace the TLS certificate before expiry.
```

---

## 17.3 TLS Expiring Within 60 Days

Condition:

```text
tls.valid is True
30 <= days_until_expiry < 60
```

Risk:

```text
Medium
```

Score:

```text
2
```

Recommendation:

```text
Schedule certificate renewal to avoid service disruption.
```

---

## 17.4 TLS Healthy

Condition:

```text
tls.valid is True
days_until_expiry >= 60
```

Risk:

```text
Informational
```

Score:

```text
0
```

Observation:

```text
TLS certificate is valid and not close to expiry.
```

---

# 18. Header Rules

Header rules must be driven primarily by the header knowledge base.

## 18.1 Known Expected Header Missing

Condition:

```text
header.expected == "present"
header.present is False
```

Finding generated from header knowledge base:

```text
title
observation
interpretation
recommendation
risk_contribution
score
```

Risk contribution comes from:

```text
risk_if_missing
score_if_missing
```

---

## 18.2 Known Optional Header Missing

Condition:

```text
header.expected == "optional"
header.present is False
```

No finding by default.

Optional headers may appear in raw evidence or expected-header summary but should not generate risk.

---

## 18.3 Known Contextual Header Missing

Condition:

```text
header.expected == "contextual"
header.present is False
```

No risk finding by default.

May generate informational observation if useful.

---

## 18.4 Known Header Present

Condition:

```text
header.present is True
```

Generate evidence.

Generate observation.

Generate finding only if:

```text
header is deprecated
header is legacy and operationally relevant
header exposes server/application detail
header value is unexpected
header participates in a combination rule
```

---

## 18.5 Deprecated Header Present

Condition:

```text
header.deprecated is True
header.present is True
```

Risk:

```text
Informational or Low
```

Recommendation:

```text
Review whether this legacy header is still required.
```

---

## 18.6 Header Present With Unexpected Value

Condition:

```text
header has recommended_values
observed value does not match expected pattern
```

Risk:

```text
Low or Medium depending on header
```

Examples:

```text
X-Content-Type-Options present but not nosniff
X-Frame-Options present but not DENY or SAMEORIGIN
```

---

# 19. Header-Specific Rules

## 19.1 HSTS Missing

Condition:

```text
Strict-Transport-Security missing
final_url starts with https://
```

Risk:

```text
Medium
```

Score:

```text
2
```

Recommendation:

```text
If HTTPS is intended to be enforced permanently, consider enabling HSTS after confirming HTTPS readiness.
```

If final URL is HTTP, do not generate the same finding. Instead, use HTTPS/canonical transport rule.

---

## 19.2 CSP Missing

Condition:

```text
Content-Security-Policy missing
```

Risk:

```text
Medium
```

Score:

```text
2
```

Recommendation:

```text
Consider defining a CSP and testing it in report-only mode.
```

---

## 19.3 X-Content-Type-Options Missing

Condition:

```text
X-Content-Type-Options missing
```

Risk:

```text
Medium
```

Score:

```text
2
```

Recommendation:

```text
Consider setting X-Content-Type-Options to nosniff.
```

---

## 19.4 X-Content-Type-Options Incorrect Value

Condition:

```text
X-Content-Type-Options present
value lowercased != "nosniff"
```

Risk:

```text
Low
```

Score:

```text
1
```

Recommendation:

```text
Review the header value and consider using nosniff.
```

---

## 19.5 X-Frame-Options Missing and No CSP frame-ancestors

Condition:

```text
X-Frame-Options missing
AND Content-Security-Policy does not contain frame-ancestors
```

Risk:

```text
Medium
```

Score:

```text
2
```

Recommendation:

```text
Consider defining framing behaviour using X-Frame-Options or CSP frame-ancestors.
```

---

## 19.6 Referrer-Policy Missing

Condition:

```text
Referrer-Policy missing
```

Risk:

```text
Low
```

Score:

```text
1
```

Recommendation:

```text
Consider setting a Referrer-Policy appropriate to privacy and analytics requirements.
```

---

## 19.7 Permissions-Policy Missing

Condition:

```text
Permissions-Policy missing
```

Risk:

```text
Low
```

Score:

```text
1
```

Recommendation:

```text
Consider defining a Permissions-Policy to restrict unused browser features.
```

---

## 19.8 Deprecated Header Present

Condition:

```text
X-XSS-Protection present
OR Public-Key-Pins present
OR Expect-CT present
OR Feature-Policy present
```

Risk:

```text
Informational or Low
```

Recommendation:

```text
Review whether this legacy header is still required and prefer modern alternatives where applicable.
```

---

# 20. Cookie Rules

Cookie rules apply only when cookies are present.

No cookies present should usually produce an informational observation only.

## 20.1 Cookie Without Secure

Condition:

```text
cookie present
final_url uses https
cookie.secure is False
```

Risk:

```text
Medium
```

Score:

```text
2
```

Recommendation:

```text
For cookies used over HTTPS, consider adding the Secure attribute where appropriate.
```

---

## 20.2 Cookie Without HttpOnly

Condition:

```text
cookie present
cookie.httponly is False
```

Risk:

```text
Medium
```

Score:

```text
2
```

Recommendation:

```text
For session or sensitive cookies, consider adding HttpOnly to reduce browser script access.
```

---

## 20.3 Cookie Without SameSite

Condition:

```text
cookie present
cookie.samesite is None
```

Risk:

```text
Low
```

Score:

```text
1
```

Recommendation:

```text
Consider setting a SameSite attribute appropriate to the site's cross-site workflow.
```

---

## 20.4 Cookie With Broad Domain

Condition:

```text
cookie.domain is present
```

Risk:

```text
Informational
```

Score:

```text
0
```

Recommendation:

```text
Review whether the cookie domain scope is intentional.
```

Notes:

Do not score unless there is a clearly broad or suspicious domain rule in a future version.

---

# 21. Cache Rules

## 21.1 No Cache Configuration Observed

Condition:

```text
cache.configured is False
```

Risk:

```text
Low
```

Score:

```text
1
```

Recommendation:

```text
Consider defining cache behaviour appropriate to the content type and freshness requirements.
```

---

## 21.2 No-Store Present

Condition:

```text
Cache-Control includes no-store
```

Risk:

```text
Informational
```

Score:

```text
0
```

Interpretation:

```text
The response instructs caches not to store the content.
```

Notes:

This may be correct for sensitive pages.

Do not treat as a problem.

---

## 21.3 Long Max-Age

Condition:

```text
Cache-Control max-age greater than 30 days
```

Risk:

```text
Informational
```

Score:

```text
0
```

Recommendation:

```text
Confirm that long-lived caching is intended for this content.
```

---

# 22. Compression Rules

## 22.1 Compression Not Observed

Condition:

```text
compression.enabled is False
content_type starts with text/
OR content_type includes html, json, javascript, css, xml
```

Risk:

```text
Low
```

Score:

```text
1
```

Recommendation:

```text
For compressible text-based content, consider enabling Brotli or gzip compression.
```

---

## 22.2 Compression Observed

Condition:

```text
compression.enabled is True
```

Risk:

```text
Informational
```

Score:

```text
0
```

Observation:

```text
The response appears to use compression.
```

---

# 23. Performance Rules

## 23.1 Large Page Weight

Condition:

```text
performance.page_weight_classification == "Large"
```

Risk:

```text
Medium
```

Score:

```text
2
```

Recommendation:

```text
Review page assets, compression, caching, and frontend payload size to improve visitor experience.
```

---

## 23.2 Moderate Page Weight

Condition:

```text
performance.page_weight_classification == "Moderate"
```

Risk:

```text
Low
```

Score:

```text
1
```

Recommendation:

```text
Review whether page weight is appropriate for the site's content and audience.
```

---

# 24. Platform Rules

## 24.1 CMS Detected

Condition:

```text
platform.detected is True
```

Risk:

```text
Informational
```

Score:

```text
0
```

Recommendation:

```text
Keep the detected platform, themes, plugins, and integrations maintained.
```

Notes:

CMS detection alone must not increase risk.

---

## 24.2 WordPress Detected

Condition:

```text
platform.name == "WordPress"
```

Risk:

```text
Informational
```

Score:

```text
0
```

Recommendation:

```text
WordPress indicators were observed. Keep core, themes, and plugins maintained.
```

Do not say:

```text
common target for attacks
```

---

# 25. HTML Metadata Rules

## 25.1 Missing Title

Condition:

```text
html.title_present is False
```

Risk:

```text
Low
```

Score:

```text
1
```

Recommendation:

```text
Consider adding a descriptive page title for usability and search presentation.
```

---

## 25.2 Missing Meta Description

Condition:

```text
html.meta_description_present is False
```

Risk:

```text
Informational
```

Score:

```text
0
```

Recommendation:

```text
Consider adding a meta description if search result presentation is important.
```

---

## 25.3 Missing Viewport

Condition:

```text
html.viewport_present is False
```

Risk:

```text
Low
```

Score:

```text
1
```

Recommendation:

```text
Consider adding a viewport meta tag for responsive display on mobile devices.
```

---

## 25.4 Generator Meta Present

Condition:

```text
html.generator is not None
```

Risk:

```text
Informational or Low
```

Score:

```text
0 or 1
```

Recommendation:

```text
Review whether generator metadata disclosure is useful or should be minimized.
```

---

# 26. Infrastructure Disclosure Rules

## 26.1 Server Header Present

Condition:

```text
Server header present
```

Risk:

```text
Low
```

Score:

```text
1
```

Recommendation:

```text
Consider minimizing detailed server version disclosure where practical.
```

Notes:

If the value is generic, such as `nginx`, keep it Low or Informational.

If it includes detailed version information, Low score may apply.

---

## 26.2 X-Powered-By Present

Condition:

```text
X-Powered-By header present
```

Risk:

```text
Low
```

Score:

```text
1
```

Recommendation:

```text
Consider suppressing unnecessary runtime or framework disclosure.
```

---

## 26.3 CDN Indicators Observed

Condition:

```text
Cloudflare, Fastly, Akamai, Vercel, Netlify, or similar headers present
```

Risk:

```text
Informational
```

Score:

```text
0
```

Recommendation:

```text
Use CDN indicators together with cache headers to understand delivery behaviour.
```

---

# 27. CORS Combination Rules

## 27.1 Wildcard Origin With Credentials

Condition:

```text
Access-Control-Allow-Origin == "*"
AND Access-Control-Allow-Credentials lowercased == "true"
```

Risk:

```text
Medium
```

Score:

```text
2
```

Observation:

```text
The response appears to allow credentialed CORS access broadly.
```

Interpretation:

```text
Credentialed cross-origin access should normally be limited to specific trusted origins.
```

Recommendation:

```text
Review whether credentialed cross-origin access should be restricted to explicitly trusted origins.
```

---

# 28. CSP Quality Rules

CSP quality analysis should remain basic in v1.2.

## 28.1 CSP Contains unsafe-inline

Condition:

```text
Content-Security-Policy contains "'unsafe-inline'"
```

Risk:

```text
Low
```

Score:

```text
1
```

Recommendation:

```text
Review whether inline script or style allowances can be reduced as the policy matures.
```

---

## 28.2 CSP Contains unsafe-eval

Condition:

```text
Content-Security-Policy contains "'unsafe-eval'"
```

Risk:

```text
Medium
```

Score:

```text
2
```

Recommendation:

```text
Review whether unsafe-eval is required by the application or third-party scripts.
```

---

## 28.3 CSP Uses Wildcard Default Source

Condition:

```text
Content-Security-Policy contains "default-src *"
```

Risk:

```text
Medium
```

Score:

```text
2
```

Recommendation:

```text
Review whether default content sources can be narrowed to trusted origins.
```

Notes:

Do not attempt comprehensive CSP parsing in v1.2.

---

# 29. Risk Aggregation

Risk aggregation should use all generated findings.

Base algorithm:

```python
score = sum(finding["score"] for finding in findings)
```

Then apply thresholds:

```text
Low: 0–4
Medium: 5–8
High: 9+
```

Then apply overrides:

```text
unreachable site → High
invalid TLS → High
TLS expiry under 30 days → High
5xx homepage response → High
```

The override should be visible in the risk summary.

Example:

```python
{
    "level": "High",
    "score": 3,
    "summary": "The website could not be reached, so configuration analysis could not be completed.",
    "contributors": ["finding.connectivity.unreachable"],
    "override": "Site unreachable"
}
```

---

# 30. Risk Summary Wording

Risk summary must be consultant-like.

Low:

```text
The website is reachable and serving content. Only minor configuration improvements or informational observations were identified.
```

Medium:

```text
The website is reachable and serving content, but several configuration improvements are recommended.
```

High:

```text
A significant operational issue was observed that may affect availability, trust, or maintenance reliability.
```

Avoid:

```text
The site is vulnerable.
The site is dangerous.
Immediate action required.
Attackers can exploit this.
```

---

# 31. Finding ID Convention

Finding IDs must be stable.

Recommended pattern:

```text
finding.<area>.<subject>.<condition>
```

Examples:

```text
finding.connectivity.unreachable
finding.tls.invalid
finding.tls.expiring_soon
finding.header.csp.missing
finding.header.hsts.missing
finding.cookie.secure.missing
finding.cache.configuration_absent
finding.performance.page_weight_large
finding.platform.cms_detected
```

Stable IDs are required for future JSON output and testing.

---

# 32. Evidence ID Convention

Evidence IDs must be stable.

Recommended pattern:

```text
<area>.<subject>
```

Examples:

```text
connectivity.reachable
connectivity.status_code
tls.valid
tls.days_until_expiry
header.content_security_policy
header.strict_transport_security
cookie.sessionid.secure
cache.cache_control
compression.content_encoding
performance.page_weight
platform.cms
html.title
```

---

# 33. Recommendation ID Convention

Recommendation IDs must be stable.

Recommended pattern:

```text
recommendation.<area>.<subject>.<action>
```

Examples:

```text
recommendation.header.csp.define_policy
recommendation.header.hsts.enable
recommendation.cookie.secure.add
recommendation.tls.renew_certificate
recommendation.performance.review_page_weight
```

---

# 34. Duplicate Finding Control

The rule engine must avoid duplicate findings.

Example:

If `X-Frame-Options` is missing but CSP contains `frame-ancestors`, do not generate a normal missing framing policy finding.

Instead, generate either:

```text
Informational: Framing behaviour appears to be controlled through CSP frame-ancestors.
```

or no finding.

The rule engine must consider interactions between related headers.

---

# 35. Finding Sorting

Findings should be sorted for report output.

Recommended order:

```text
High
Medium
Low
Informational
```

Within each group:

```text
Connectivity
TLS
Security & Browser Protection
Cookies
Caching
Compression
Performance
Infrastructure
Platform
HTML
Other
```

This ensures the report is useful and readable.

---

# 36. Rule Testing Requirements

Each rule should be testable with synthetic data.

Examples:

```text
Given CSP missing, expect finding.header.csp.missing.
Given CSP present, no missing CSP finding.
Given X-Content-Type-Options: nosniff, no incorrect-value finding.
Given X-Content-Type-Options: invalid, expect incorrect-value finding.
Given Set-Cookie without Secure over HTTPS, expect cookie secure finding.
Given no cookies, expect no cookie risk finding.
Given unreachable site, expect High override.
```

Codex should design rule functions with this future testing in mind.

---

# 37. Implementation Priority for Volume V

Codex should implement interpretation in phases.

## Phase 1

Preserve current `analyze_risk` behaviour while improving wording.

## Phase 2

Introduce structured findings.

## Phase 3

Generate findings for current checks.

## Phase 4

Move header findings to knowledge-base-driven rules.

## Phase 5

Add cookie-specific findings.

## Phase 6

Add TLS and connectivity overrides.

## Phase 7

Add combination rules.

## Phase 8

Generate risk summary from findings.

---

# 38. Success Criteria for Volume V

The rule engine is successful if:

```text
Every finding is traceable to evidence.
Risk is calculated from findings.
High risk remains rare and defensible.
Unknown headers do not create risk.
CMS detection alone does not create risk.
Cookie absence does not create risk.
Optional header absence does not create risk.
Deprecated headers are explained carefully.
The report sounds like a consultant, not an exploit scanner.
Codex can add new rules without rewriting scanner logic.
```

---

# 39. Final Rule Engine Principle

The rule engine should help users understand configuration meaning.

It should not frighten users.

It should not replace professional judgement.

It should organize evidence, explain implications, and recommend practical review steps.

Site Inspector is not a judge.

It is an evidence-based operational consultant.
