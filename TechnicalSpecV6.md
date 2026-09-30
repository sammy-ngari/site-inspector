# Site Inspector Technical Design Specification (TDS)

**Volume VI — Reporting, CLI Output & JSON Output**

**Document Version:** 1.0
**Project Version Covered:** Target v1.2
**Status:** Authoritative Engineering Specification
**Depends On:** Volume I — Project Constitution
**Depends On:** Volume II — System Architecture & Implementation Model
**Depends On:** Volume III — Data Models & Schemas
**Depends On:** Volume IV — Header Knowledge Base
**Depends On:** Volume V — Rule Engine, Findings & Risk Interpretation

---

# 1. Purpose of this Volume

This volume defines how Site Inspector presents results to users.

The reporting layer is responsible for turning structured scan results into useful, readable output.

It must preserve the evidence-first philosophy of the project while making the report understandable to both technical and semi-technical users.

The report should feel like a professional operational assessment, not a raw dump and not an alarmist scanner report.

The output must answer four questions:

```text
What was observed?
What does it mean?
What should be reviewed?
What is the overall operational condition?
```

---

# 2. Reporting Philosophy

Site Inspector reports must be hierarchical.

The user should be able to read the top of the report and understand the operational summary, then continue downward for technical detail.

The report must not force every user to start with raw headers.

The report must not hide raw evidence either.

The correct structure is:

```text
Summary first.
Evidence second.
Interpretation third.
Raw evidence last.
```

The report should be clear enough for a website owner, but precise enough for a developer or hosting administrator.

---

# 3. Reporting Tone

The report must use consultant-style language.

Preferred language:

```text
Configuration improvement recommended.
Review recommended.
Consider enabling...
Confirm whether this is intentional.
No action may be required if this behaviour is expected.
Operational review recommended.
Maintenance review recommended.
```

Avoid language:

```text
Critical vulnerability.
Dangerous.
Exploitable.
Attackers can exploit this.
Your site is unsafe.
You have been hacked.
Immediate remediation required.
```

Site Inspector may say something is a significant operational issue when the evidence supports it, such as site unreachability, invalid TLS, or severe server errors.

---

# 4. Default Console Output

The default output should be human-readable console text.

Default command:

```bash
python main.py --domain example.com
```

The default report should include:

```text
Banner
Executive Summary
Target & Request
Connectivity
Transport Security
HTTP Response
Header Overview
Header Categories
Cookies & Sessions
Cache & Freshness
Compression & Transfer
Infrastructure Indicators
Platform Detection
HTML Metadata
Performance Indicators
Operational Findings
Recommendations
Raw Evidence Summary
```

Raw evidence should be present, but the default console output may summarize it unless the user requests verbose output in a future version.

---

# 5. CLI Interface

Version 1.2 must preserve the existing v1.1 commands.

Required:

```bash
python main.py
python main.py --domain example.com
python main.py --version
```

Optional v1.2 additions:

```bash
python main.py --domain example.com --json
python main.py --domain example.com --raw
python main.py --domain example.com --no-banner
```

`--json` may be implemented in v1.2 after the structured scan result is stable.

`--raw` may expose more complete raw evidence in console output.

`--no-banner` is optional and useful for scripting.

Do not remove the interactive prompt.

---

# 6. Banner Specification

Default banner:

```text
============================================================
                       SITE INSPECTOR
          Passive Website Configuration Auditor
                       Version: v1.2
             Created & Maintained by Sammy Ngari
============================================================
```

The banner must remain professional and minimal.

It should not include dramatic security language.

If `--json` is used, the banner must not print unless explicitly requested, because JSON output must be machine-readable.

---

# 7. Executive Summary

The executive summary is the first meaningful report section.

It should include:

```text
Overall Risk Level
Short operational summary
Top 3 findings by importance
Recommended next action
Passive analysis notice
```

Example:

```text
===== EXECUTIVE SUMMARY =====

Overall Risk Level: Medium

The website is reachable and serving content, but several configuration improvements are recommended. The most important items relate to browser protection headers, cookie attributes, and cache configuration.

Top Findings:
1. Content-Security-Policy header not observed
2. Strict-Transport-Security header not observed
3. Cache-Control header not observed

Recommended Next Action:
Review the listed configuration findings with the developer, hosting provider, or system administrator.

Analysis Scope:
This analysis is based solely on publicly exposed configuration observed during a standard page request.
```

The executive summary must never imply that active security testing was performed.

---

# 8. Target & Request Section

Purpose:

Show what was inspected and how.

Required fields:

```text
Input
Normalized URL
Hostname
Final URL
Request Method
Timeout
Redirects Enabled
Single Request Model
```

Example:

```text
===== TARGET & REQUEST =====

Input: example.com
Normalized URL: https://example.com
Hostname: example.com
Final URL: https://www.example.com/
Request Method: GET
Timeout: 10 seconds
Redirects Enabled: Yes
Single Request Model: Yes
```

This section reinforces the passive model.

---

# 9. Connectivity Section

Purpose:

Show availability and response behaviour.

Required fields:

```text
Reachable
Status Code
Response Time
Redirect Count
Redirect Chain
```

Example:

```text
===== CONNECTIVITY =====

Reachable: Yes
Status Code: 200
Response Time: 1.24 seconds
Redirect Count: 1

Redirect Chain:
1. 301 https://example.com → https://www.example.com/
```

If unreachable:

```text
===== CONNECTIVITY =====

Reachable: No

The website could not be reached during the request. Configuration analysis could not be completed.
```

Unreachable sites should still produce a structured report where possible.

---

# 10. Transport Security Section

Purpose:

Show TLS certificate evidence.

Required fields:

```text
TLS Checked
Certificate Valid
Days Until Expiry
Not Before
Not After
Issuer
Subject
TLS Error
```

Example:

```text
===== TRANSPORT SECURITY =====

TLS Checked: Yes
Certificate Valid: Yes
Days Until Expiry: 82
Issuer: Example Certificate Authority
Subject: example.com
```

If TLS fails:

```text
===== TRANSPORT SECURITY =====

TLS Checked: Yes
Certificate Valid: No
Error: TLS certificate could not be verified

Operational Note:
Review certificate installation, hostname coverage, certificate chain, and expiry status.
```

The section should not use the phrase “site is insecure” by default.

---

# 11. HTTP Response Section

Purpose:

Show the basic final response metadata.

Required fields:

```text
Final Status Code
Content-Type
Content-Length
Observed Payload Size
Content-Encoding
Body Present
```

Example:

```text
===== HTTP RESPONSE =====

Status Code: 200
Content-Type: text/html; charset=UTF-8
Content-Length: 125000
Payload Size: 122.1 KB
Content-Encoding: br
Body Present: Yes
```

If content length is absent:

```text
Content-Length: Not declared
```

---

# 12. Header Overview Section

Purpose:

Summarize all observed response headers.

Required fields:

```text
Total Observed Headers
Known Observed Headers
Unknown Observed Headers
Expected Known Headers Missing
Deprecated Headers Observed
```

Example:

```text
===== HEADER OVERVIEW =====

Total Observed Headers: 18
Known Observed Headers: 14
Unknown Observed Headers: 4
Expected Known Headers Missing: 3
Deprecated Headers Observed: 1
```

This section must make clear that unknown headers are preserved.

---

# 13. Header Category Sections

Purpose:

Present all headers by category.

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
Reporting & Monitoring
Legacy / Deprecated Headers
Vendor-Specific / Unclassified
```

Each category should show only relevant entries.

Empty categories may either be omitted or shown as:

```text
No observed headers in this category.
```

Preferred v1.2 behaviour:

Show categories that contain observed headers or expected missing headers.

---

# 14. Header Entry Format

Each header entry should use this format:

```text
Header: Content-Security-Policy
Status: Missing
Category: Security & Browser Protection
Interpretation: The response does not include a site-defined content policy.
Recommendation: Consider defining a Content-Security-Policy appropriate to the application and testing it in report-only mode.
Risk Contribution: Medium
```

Observed header example:

```text
Header: Cache-Control
Value: max-age=3600
Status: Observed
Category: Caching & Freshness
Interpretation: The response includes cache behaviour instructions.
Recommendation: Review whether the directives match the content's expected freshness and privacy requirements.
Risk Contribution: Informational
```

Unknown header example:

```text
Header: X-Custom-Edge
Value: edge-01
Status: Observed
Category: Vendor-Specific / Unclassified
Interpretation: Header observed but not classified by Site Inspector.
Risk Contribution: Informational
```

Unknown headers must never be hidden.

---

# 15. Security & Browser Protection Section

This section should receive special attention because it is commonly useful.

It should include, when present or expected:

```text
Strict-Transport-Security
Content-Security-Policy
Content-Security-Policy-Report-Only
X-Content-Type-Options
X-Frame-Options
Referrer-Policy
Permissions-Policy
Cross-Origin-Opener-Policy
Cross-Origin-Resource-Policy
Cross-Origin-Embedder-Policy
```

The section should clearly distinguish between:

```text
Observed
Missing
Observed with expected value
Observed with unexpected value
Contextual
Legacy
Deprecated
```

---

# 16. Cookies & Sessions Section

Purpose:

Show cookie configuration.

Required fields:

```text
Cookies Present
Total Cookies
Secure Count
HttpOnly Count
SameSite Count
Missing Secure Count
Missing HttpOnly Count
Missing SameSite Count
```

Example:

```text
===== COOKIES & SESSIONS =====

Cookies Present: Yes
Total Cookies: 2
Cookies with Secure: 1
Cookies with HttpOnly: 2
Cookies with SameSite: 1

Cookie Details:
1. sessionid
   Secure: Missing
   HttpOnly: Present
   SameSite: Lax
   Path: /
```

If no cookies:

```text
===== COOKIES & SESSIONS =====

Cookies Present: No

No Set-Cookie header was observed in the primary response. This is not automatically a problem.
```

---

# 17. Cache & Freshness Section

Purpose:

Show browser and intermediary cache indicators.

Required fields:

```text
Cache-Control
Expires
ETag
Last-Modified
Vary
Configured
Parsed Directives
```

Example:

```text
===== CACHE & FRESHNESS =====

Cache-Control: max-age=3600
Expires: Not observed
ETag: "abc123"
Last-Modified: Mon, 01 Jan 2026 10:00:00 GMT
Vary: Accept-Encoding
Cache Configuration Observed: Yes
```

The section should avoid claiming that a cache policy is wrong unless evidence is clear.

---

# 18. Compression & Transfer Section

Purpose:

Show response compression and transfer metadata.

Required fields:

```text
Compression Enabled
Compression Method
Content-Encoding
Transfer-Encoding
Content-Length
Accept-Ranges
```

Example:

```text
===== COMPRESSION & TRANSFER =====

Compression Enabled: Yes
Compression Method: br
Content-Encoding: br
Transfer-Encoding: Not observed
Accept-Ranges: bytes
```

If compression is absent:

```text
Compression Enabled: No
Operational Note: For compressible text-based content, compression may improve visitor experience.
```

---

# 19. Infrastructure Indicators Section

Purpose:

Show infrastructure hints without overclaiming.

Required fields:

```text
Server
X-Powered-By
Via
CDN Indicators
Proxy Indicators
Edge Indicators
HTTP/3 Hint
Raw Headers Used
```

Example:

```text
===== INFRASTRUCTURE INDICATORS =====

Server: nginx
X-Powered-By: Not disclosed
Via: Not observed

CDN / Edge Indicators:
- Cloudflare indicators observed through CF-Ray header.

HTTP/3 Hint:
- Alt-Svc header observed. This may indicate alternative protocol support.
```

Use cautious wording.

Do not say “definitely uses” unless the evidence is definitive and the wording remains conservative.

---

# 20. Platform Detection Section

Purpose:

Show CMS or platform indicators found in returned HTML.

Required fields:

```text
Detected
Name
Confidence
Evidence
```

Example:

```text
===== PLATFORM DETECTION =====

Detected Platform: WordPress
Confidence: Medium

Evidence:
- wp-content marker found in returned HTML

Operational Note:
Keep the detected platform, themes, plugins, and integrations maintained.
```

If unknown:

```text
Detected Platform: Unknown
Confidence: None
```

CMS detection alone must not be treated as a risk issue.

---

# 21. HTML Metadata Section

Purpose:

Show useful metadata from the returned HTML.

Required fields:

```text
Title
Title Present
Meta Description Present
Canonical Present
Canonical URL
Viewport Present
Charset
Generator
Script Count
Stylesheet Count
```

Example:

```text
===== HTML METADATA =====

Title: Example Website
Meta Description Present: Yes
Canonical Present: Yes
Canonical URL: https://www.example.com/
Viewport Present: Yes
Charset: UTF-8
Generator: WordPress 6.x
Script Count: 12
Stylesheet Count: 4
```

This section should remain operational, not SEO-audit-heavy.

---

# 22. Performance Indicators Section

Purpose:

Show basic performance indicators available from one response.

Required fields:

```text
Response Time
Payload Size
Page Weight Classification
Compression Enabled
Cache Configured
```

Example:

```text
===== PERFORMANCE INDICATORS =====

Response Time: 1.24 seconds
Payload Size: 122.1 KB
Page Weight: Small
Compression Enabled: Yes
Cache Configured: Yes
```

Required disclaimer:

```text
This is not a full performance test. It is based on the primary response observed during this inspection.
```

---

# 23. Operational Findings Section

Purpose:

Show generated findings sorted by importance.

Sorting order:

```text
High
Medium
Low
Informational
```

Within each level:

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

Finding format:

```text
[Medium] Content-Security-Policy header not observed

Evidence:
- Header: Content-Security-Policy
- Observed Value: Not present

Observation:
The response does not include a Content-Security-Policy header.

Interpretation:
The browser is not receiving a site-defined policy for restricting permitted content sources.

Recommendation:
Consider defining a Content-Security-Policy appropriate to the application after testing it in report-only mode.
```

Findings should be detailed enough to be useful, but not written like a vulnerability database.

---

# 24. Recommendations Section

Purpose:

Summarize practical next actions.

Recommendations should be grouped by priority.

Example:

```text
===== RECOMMENDATIONS =====

High Priority:
- Renew or replace the TLS certificate before expiry.

Medium Priority:
- Consider defining a Content-Security-Policy and testing it in report-only mode.
- Consider enabling Strict-Transport-Security after confirming HTTPS readiness.

Low Priority:
- Consider setting a Referrer-Policy appropriate to privacy and analytics requirements.
- Consider minimizing detailed server version disclosure where practical.
```

If no meaningful recommendations exist:

```text
No major configuration recommendations were generated from the observed response.
```

---

# 25. Raw Evidence Summary Section

Purpose:

Expose raw evidence without overwhelming default users.

Default console output should show:

```text
Raw headers observed
Final URL
Status code
Redirect count
Payload size
TLS status
```

Example:

```text
===== RAW EVIDENCE SUMMARY =====

Raw Headers Observed:
- Content-Type: text/html; charset=UTF-8
- Cache-Control: max-age=3600
- Server: nginx
- X-Custom-Edge: edge-01
```

If `--raw` is implemented, it may show more complete structured raw evidence.

Do not print the full HTML response by default.

---

# 26. Passive Analysis Notice

Every report must include this notice near the top or bottom:

```text
This analysis is based solely on publicly exposed configuration observed during a standard page request.
```

The notice reinforces project scope and prevents misunderstanding.

---

# 27. JSON Output

JSON output must be generated from the same `ScanResult` object as console output.

Command:

```bash
python main.py --domain example.com --json
```

Rules:

```text
Do not print banner.
Do not print human-readable sections.
Do not include ANSI formatting.
Do not include console-only headings.
Return valid JSON.
```

JSON must include:

```text
project
target
request
connectivity
tls
response
headers
cookies
cache
compression
infrastructure
platform
html
performance
evidence
observations
findings
recommendations
risk
errors
```

JSON output must be suitable for future API usage, monitoring, or storage.

---

# 28. JSON Example

Example abbreviated JSON:

```json
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
    "redirects_enabled": true,
    "single_request_model": true,
    "user_agent": null
  },
  "connectivity": {
    "reachable": true,
    "status_code": 200,
    "response_time_seconds": 1.24,
    "redirect_count": 1,
    "redirect_chain": []
  },
  "risk": {
    "level": "Medium",
    "score": 6,
    "summary": "The website is reachable and serving content, but several configuration improvements are recommended.",
    "contributors": [
      "finding.header.csp.missing",
      "finding.header.hsts.missing"
    ]
  }
}
```

---

# 29. Report Generation Architecture

The report layer should receive a complete `scan_result`.

Preferred function:

```python
def print_report(scan_result: dict) -> None:
    ...
```

Optional helper functions:

```python
print_banner()
print_executive_summary(scan_result)
print_target_section(scan_result)
print_connectivity_section(scan_result)
print_tls_section(scan_result)
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
```

Each helper should only format data.

No helper should collect evidence or calculate risk.

---

# 30. Report Layer Rules

The report layer must not:

```text
make network requests
parse raw HTML for CMS
calculate TLS expiry
calculate risk scores
modify evidence
hide unknown headers
generate new findings
```

The report layer may:

```text
sort findings
format values
replace None with "Not observed"
convert booleans into Yes/No
group recommendations
print section headers
```

---

# 31. Formatting Rules

Use consistent section headings.

Preferred:

```text
===== SECTION TITLE =====
```

Use blank lines between sections.

Avoid excessive ASCII art after the banner.

Use simple indentation for nested detail.

Example:

```text
Cookie Details:
1. sessionid
   Secure: Present
   HttpOnly: Present
   SameSite: Lax
```

Do not use color in v1.2 unless explicitly approved.

Plain text output should work across terminals.

---

# 32. Value Rendering Rules

The report layer should render values consistently.

Python value:

```python
None
```

Console output:

```text
Not observed
```

Boolean `True`:

```text
Yes
```

Boolean `False`:

```text
No
```

Empty list:

```text
None observed
```

Empty string:

```text
Not observed
```

Large byte values should also show KB.

Example:

```text
125000 bytes (122.1 KB)
```

---

# 33. Failed Scan Report

If the site is unreachable, the report should still be structured.

Example:

```text
===== EXECUTIVE SUMMARY =====

Overall Risk Level: High

The website could not be reached during the request. Configuration analysis could not be completed.

Recommended Next Action:
Confirm DNS, hosting availability, firewall rules, and server health.

Analysis Scope:
This analysis is based solely on publicly exposed configuration observed during a standard page request.

===== TARGET & REQUEST =====

Input: bad-example.invalid
Normalized URL: https://bad-example.invalid
Hostname: bad-example.invalid
Request Method: GET
Timeout: 10 seconds

===== CONNECTIVITY =====

Reachable: No
Error: Request failed or timed out
```

Do not crash.

Do not attempt extra checks.

---

# 34. Version Output

Command:

```bash
python main.py --version
```

Expected output:

```text
Site Inspector v1.2
```

No scan should be performed.

The version output may include the banner only if current behaviour requires it, but preferred v1.2 behaviour is clean version output without full report.

---

# 35. Interactive Mode

Command:

```bash
python main.py
```

Expected prompt:

```text
Enter a domain to inspect (e.g., example.com):
```

Preferred wording:

Use “inspect” rather than “scan” where practical.

Acceptable:

```text
Enter a domain to scan
```

But long-term language should favor:

```text
inspect
analyze
review
audit
```

---

# 36. Domain Argument Mode

Command:

```bash
python main.py --domain example.com
```

Expected behaviour:

```text
No prompt.
Run inspection.
Print report.
```

If domain is empty or missing:

```text
Show helpful CLI error.
```

---

# 37. JSON Mode Error Handling

If `--json` is used and an error occurs, output must still be valid JSON.

Example:

```json
{
  "project": {
    "name": "Site Inspector",
    "version": "v1.2"
  },
  "target": {
    "input": "bad-example.invalid",
    "normalized_url": "https://bad-example.invalid",
    "hostname": "bad-example.invalid",
    "final_url": null
  },
  "connectivity": {
    "reachable": false
  },
  "errors": [
    {
      "component": "http",
      "message": "Request failed or timed out",
      "recoverable": true,
      "exception_type": "RequestException"
    }
  ],
  "risk": {
    "level": "High",
    "summary": "The website could not be reached, so configuration analysis could not be completed."
  }
}
```

Do not print Python tracebacks in JSON mode.

---

# 38. Report Completeness Requirements

The console report must include every major section unless the scan fails before data exists.

For successful scans, the report must show:

```text
target
connectivity
tls
response
headers
cookies
cache
compression
infrastructure
platform
html
performance
findings
recommendations
raw evidence summary
```

If a section has no data, show a clear statement.

Example:

```text
No cookies were observed in the primary response.
```

---

# 39. Header Completeness Requirements

Every observed header must appear somewhere in the report.

Known headers appear under their category.

Unknown headers appear under:

```text
Vendor-Specific / Unclassified
```

Expected but missing known headers appear in the relevant category if they are configured as expected headers in the knowledge base.

Do not silently drop headers.

---

# 40. Findings Completeness Requirements

Every generated finding must appear in:

```text
Operational Findings
```

Every recommendation attached to a finding must appear in:

```text
Recommendations
```

The same recommendation should not be repeated unnecessarily.

Deduplicate recommendations by ID.

---

# 41. Consultant-Style Examples

Good:

```text
The response does not include a Referrer-Policy header. Consider setting a policy appropriate to the site's privacy and analytics requirements.
```

Bad:

```text
Missing Referrer-Policy exposes users to information leakage attacks.
```

Good:

```text
The Server header is present. Consider minimizing detailed version disclosure where practical.
```

Bad:

```text
Server disclosure lets attackers fingerprint your system.
```

Good:

```text
WordPress indicators were observed. Keep core, themes, and plugins maintained.
```

Bad:

```text
WordPress is a common attack target.
```

---

# 42. Report Length Management

Because v1.2 collects many headers, output may become long.

Default report should prioritize readability.

Recommended approach:

```text
Executive Summary: concise
Findings: detailed
Header Categories: summarized but complete
Raw Evidence: complete header list, no full HTML
```

Future options may include:

```bash
--summary
--verbose
--raw
```

Do not implement these unless explicitly requested.

---

# 43. Machine Readability

The report layer and JSON layer must not duplicate scan logic.

Both outputs must come from the same `ScanResult`.

Correct:

```text
scan_result → console report
scan_result → JSON output
```

Incorrect:

```text
console scan logic
JSON scan logic
```

This ensures consistency.

---

# 44. Acceptance Criteria for Volume VI

The reporting layer is successful if:

```text
The report is hierarchical.
The executive summary is understandable.
The technical sections are complete.
Every observed header appears somewhere.
Unknown headers are preserved.
Findings are traceable to evidence.
Recommendations are practical and restrained.
JSON output is valid when enabled.
Failed scans produce structured output.
The report clearly states the passive analysis scope.
The tone remains professional and non-alarmist.
```

---

# 45. Final Reporting Rule

Site Inspector must report with clarity, restraint, and completeness.

The user should leave the report understanding what was observed, what it generally means, and what deserves review.

The report should inform judgement.

It should not manufacture fear.
