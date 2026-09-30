# Site Inspector Technical Design Specification (TDS)

**Volume IV — Header Knowledge Base**

**Document Version:** 1.0
**Project Version Covered:** Target v1.2
**Status:** Authoritative Engineering Specification
**Depends On:** Volume I — Project Constitution
**Depends On:** Volume II — System Architecture & Implementation Model
**Depends On:** Volume III — Data Models & Schemas

---

# 1. Purpose of this Volume

This volume defines the HTTP response header intelligence layer for Site Inspector.

The purpose of the header knowledge base is to ensure that Site Inspector does not merely check a small list of headers, but instead collects every response header, categorizes every observed header, explains known headers, preserves unknown headers, and generates conservative operational findings where appropriate.

The header knowledge base is not a vulnerability database.

It is a configuration interpretation reference.

It exists to help Site Inspector answer the following questions:

What headers were observed?

What category does each header belong to?

What does each known header generally mean?

Is the header modern, legacy, deprecated, vendor-specific, or unclassified?

Does the header have an operational interpretation?

Does the header contribute to risk scoring?

What recommendation, if any, should be generated?

---

# 2. Core Header Philosophy

Site Inspector must collect all response headers returned by the primary HTTP GET request.

It must not restrict itself to a small checklist.

It must not discard unknown headers.

It must not assume that a missing header is automatically a serious issue.

It must separate header evidence from header interpretation.

The correct workflow is:

```text
Collect all response headers.
Normalize header names.
Preserve raw names and values.
Categorize known headers.
Place unknown headers into Vendor-Specific / Unclassified.
Generate factual observations.
Generate conservative interpretations.
Generate findings only where appropriate.
Score only findings with clear operational meaning.
```

---

# 3. Header Knowledge Base Implementation Model

The header knowledge base should be implemented as a deterministic data structure.

Recommended file:

```text
knowledge_base/headers.py
```

Alternative acceptable v1.2 location during transition:

```text
scanner.py
```

Preferred structure:

```python
HEADER_KNOWLEDGE_BASE = {
    "content-security-policy": {
        "canonical_name": "Content-Security-Policy",
        "category": "Security & Browser Protection",
        "purpose": "...",
        "expected": "present",
        "recommended_values": [],
        "deprecated": False,
        "legacy": False,
        "risk_if_missing": "Medium",
        "score_if_missing": 2,
        "risk_if_present": "Informational",
        "score_if_present": 0,
        "interpretation_present": "...",
        "interpretation_missing": "...",
        "recommendation_missing": "...",
        "notes": "..."
    }
}
```

All lookup keys must be lowercase.

The `canonical_name` field must preserve the standard display name.

---

# 4. Header Entry Schema

Each known header entry must follow this schema.

```python
{
    "canonical_name": "Header-Name",
    "normalized_name": "header-name",
    "category": "Category Name",
    "purpose": "Short explanation of what the header communicates.",
    "expected": "present | optional | contextual | legacy | deprecated",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "Informational | Low | Medium | High | None",
    "score_if_missing": 0,
    "risk_if_present": "Informational | Low | Medium | High | None",
    "score_if_present": 0,
    "interpretation_present": "Consultant-style interpretation when observed.",
    "interpretation_missing": "Consultant-style interpretation when expected but not observed.",
    "recommendation_missing": "Conservative recommendation if absent.",
    "recommendation_present": None,
    "notes": "Additional implementation guidance."
}
```

Required fields:

```text
canonical_name
normalized_name
category
purpose
expected
recommended_values
deprecated
legacy
risk_if_missing
score_if_missing
risk_if_present
score_if_present
interpretation_present
interpretation_missing
recommendation_missing
recommendation_present
notes
```

---

# 5. Required Header Categories

Every known header must belong to one of these categories.

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

The category names must remain stable.

The report layer may display friendly names, but internal keys should remain predictable.

Suggested internal category keys:

```python
HEADER_CATEGORIES = {
    "security_browser_protection": "Security & Browser Protection",
    "caching_freshness": "Caching & Freshness",
    "compression_transfer": "Compression & Transfer",
    "content_metadata": "Content Metadata",
    "cookies_sessions": "Cookies & Sessions",
    "redirect_location": "Redirect & Location",
    "cors_cross_origin_access": "CORS & Cross-Origin Access",
    "cdn_proxy_edge_infrastructure": "CDN / Proxy / Edge Infrastructure",
    "server_application_disclosure": "Server / Application Disclosure",
    "protocol_connection_behaviour": "Protocol / Connection Behaviour",
    "reporting_monitoring": "Reporting & Monitoring",
    "legacy_deprecated": "Legacy / Deprecated Headers",
    "vendor_specific_unclassified": "Vendor-Specific / Unclassified"
}
```

---

# 6. Risk Scoring Rules for Headers

Header risk scoring must remain conservative.

The header knowledge base may define missing-header or present-header scores, but the risk engine must apply them carefully.

Suggested scoring:

```text
Informational: 0
Low: 1
Medium: 2
High: 3
```

High header findings should be rare.

Missing a single browser protection header should usually not be High.

High risk should be reserved for severe operational conditions, such as invalid TLS, unreachable site, or serious misconfiguration with strong evidence.

Header findings usually produce Low or Medium contributions.

---

# 7. Value Validation Rules

Site Inspector should distinguish between:

```text
Header missing
Header present with any value
Header present with recommended value
Header present with legacy/deprecated value
Header present with potentially weak value
```

Example:

```text
X-Content-Type-Options: nosniff
```

This should be interpreted as correctly configured.

Example:

```text
X-Content-Type-Options: something-else
```

This should be interpreted as present but not using the expected value.

Do not treat all present headers as equally configured.

However, Version 1.2 should remain conservative and should avoid deep validation where header semantics are complex.

---

# 8. Unknown Header Handling

Any header not found in the knowledge base must still be preserved.

Unknown header object:

```python
{
    "name": "X-Custom-Edge",
    "normalized_name": "x-custom-edge",
    "value": "edge-01",
    "present": True,
    "known": False,
    "category": "Vendor-Specific / Unclassified",
    "deprecated": False,
    "legacy": False,
    "purpose": None,
    "interpretation": "Header observed but not classified by Site Inspector.",
    "recommendation": None,
    "risk_contribution": "Informational",
    "score": 0
}
```

Unknown headers must never be hidden.

Unknown headers must not contribute to risk unless a future rule explicitly classifies them.

---

# 9. Security & Browser Protection Headers

These headers describe browser-side protection, transport enforcement, resource restrictions, framing policy, referrer handling, and browser feature access.

## 9.1 Strict-Transport-Security

```python
{
    "canonical_name": "Strict-Transport-Security",
    "normalized_name": "strict-transport-security",
    "category": "Security & Browser Protection",
    "purpose": "Instructs browsers to access the host only over HTTPS for a defined period.",
    "expected": "present",
    "recommended_values": ["max-age=<seconds>", "includeSubDomains", "preload"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "Medium",
    "score_if_missing": 2,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response advertises an HSTS policy for future browser connections.",
    "interpretation_missing": "The response does not advertise an HSTS policy.",
    "recommendation_missing": "If HTTPS is intended to be enforced permanently, consider enabling Strict-Transport-Security after confirming that the site and subdomains are HTTPS-ready.",
    "recommendation_present": "Review the max-age value and whether includeSubDomains is appropriate for this domain.",
    "notes": "Do not recommend includeSubDomains blindly. It may affect subdomains."
}
```

## 9.2 Content-Security-Policy

```python
{
    "canonical_name": "Content-Security-Policy",
    "normalized_name": "content-security-policy",
    "category": "Security & Browser Protection",
    "purpose": "Defines browser-enforced restrictions for permitted content sources.",
    "expected": "present",
    "recommended_values": ["default-src", "script-src", "style-src", "img-src", "object-src", "base-uri", "frame-ancestors"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "Medium",
    "score_if_missing": 2,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response includes a Content-Security-Policy header.",
    "interpretation_missing": "The response does not include a site-defined content policy.",
    "recommendation_missing": "Consider defining a Content-Security-Policy appropriate to the application and testing it in report-only mode before enforcement.",
    "recommendation_present": "Review the policy for overly broad directives such as unsafe-inline, unsafe-eval, or wildcard sources.",
    "notes": "Deep CSP quality scoring should be added gradually. Presence alone does not guarantee a strong policy."
}
```

## 9.3 Content-Security-Policy-Report-Only

```python
{
    "canonical_name": "Content-Security-Policy-Report-Only",
    "normalized_name": "content-security-policy-report-only",
    "category": "Security & Browser Protection",
    "purpose": "Allows CSP testing by reporting violations without enforcing restrictions.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response includes a report-only CSP policy, which may indicate staged policy testing.",
    "interpretation_missing": "No report-only CSP policy was observed.",
    "recommendation_missing": None,
    "recommendation_present": "If a full CSP is not yet enforced, report-only mode can support safe policy testing.",
    "notes": "Do not treat absence as a problem."
}
```

## 9.4 X-Content-Type-Options

```python
{
    "canonical_name": "X-Content-Type-Options",
    "normalized_name": "x-content-type-options",
    "category": "Security & Browser Protection",
    "purpose": "Instructs browsers not to MIME-sniff responses away from the declared Content-Type.",
    "expected": "present",
    "recommended_values": ["nosniff"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "Medium",
    "score_if_missing": 2,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response includes MIME-sniffing protection.",
    "interpretation_missing": "The response does not include X-Content-Type-Options.",
    "recommendation_missing": "Consider setting X-Content-Type-Options to nosniff.",
    "recommendation_present": "Confirm the value is nosniff.",
    "notes": "Value validation should check for nosniff."
}
```

## 9.5 X-Frame-Options

```python
{
    "canonical_name": "X-Frame-Options",
    "normalized_name": "x-frame-options",
    "category": "Security & Browser Protection",
    "purpose": "Controls whether the page may be displayed inside a frame.",
    "expected": "present",
    "recommended_values": ["DENY", "SAMEORIGIN"],
    "deprecated": False,
    "legacy": True,
    "risk_if_missing": "Medium",
    "score_if_missing": 2,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response includes a framing policy through X-Frame-Options.",
    "interpretation_missing": "The response does not include an X-Frame-Options header.",
    "recommendation_missing": "Consider defining framing behaviour using either X-Frame-Options or the CSP frame-ancestors directive.",
    "recommendation_present": "Confirm the value is DENY or SAMEORIGIN unless another framing policy is intentional.",
    "notes": "Modern CSP frame-ancestors can provide more flexible framing control."
}
```

## 9.6 Referrer-Policy

```python
{
    "canonical_name": "Referrer-Policy",
    "normalized_name": "referrer-policy",
    "category": "Security & Browser Protection",
    "purpose": "Controls how much referrer information browsers send with outbound requests.",
    "expected": "present",
    "recommended_values": ["strict-origin-when-cross-origin", "no-referrer", "same-origin"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "Low",
    "score_if_missing": 1,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response defines how referrer information should be shared.",
    "interpretation_missing": "The response does not define a Referrer-Policy.",
    "recommendation_missing": "Consider setting a Referrer-Policy appropriate to the site's privacy and analytics requirements.",
    "recommendation_present": "Review whether the selected policy matches privacy and analytics expectations.",
    "notes": "Missing Referrer-Policy is usually low severity."
}
```

## 9.7 Permissions-Policy

```python
{
    "canonical_name": "Permissions-Policy",
    "normalized_name": "permissions-policy",
    "category": "Security & Browser Protection",
    "purpose": "Controls access to selected browser features such as camera, microphone, geolocation, and fullscreen.",
    "expected": "present",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "Low",
    "score_if_missing": 1,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response includes a browser feature permissions policy.",
    "interpretation_missing": "The response does not include a Permissions-Policy header.",
    "recommendation_missing": "Consider defining a Permissions-Policy to restrict browser features that the site does not require.",
    "recommendation_present": "Review whether the policy restricts unused browser capabilities.",
    "notes": "Absence is usually a configuration improvement opportunity, not a major issue."
}
```

## 9.8 Cross-Origin-Opener-Policy

```python
{
    "canonical_name": "Cross-Origin-Opener-Policy",
    "normalized_name": "cross-origin-opener-policy",
    "category": "Security & Browser Protection",
    "purpose": "Controls browsing context isolation between documents.",
    "expected": "contextual",
    "recommended_values": ["same-origin", "same-origin-allow-popups", "unsafe-none"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "Low",
    "score_if_missing": 1,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response defines cross-origin opener behaviour.",
    "interpretation_missing": "No Cross-Origin-Opener-Policy header was observed.",
    "recommendation_missing": "For applications that need stronger cross-origin isolation, review whether COOP should be configured.",
    "recommendation_present": "Confirm the selected COOP value matches the application's cross-origin behaviour.",
    "notes": "Contextual. Do not treat absence as severe."
}
```

## 9.9 Cross-Origin-Resource-Policy

```python
{
    "canonical_name": "Cross-Origin-Resource-Policy",
    "normalized_name": "cross-origin-resource-policy",
    "category": "Security & Browser Protection",
    "purpose": "Controls whether other origins may embed or load the resource.",
    "expected": "contextual",
    "recommended_values": ["same-origin", "same-site", "cross-origin"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "Low",
    "score_if_missing": 1,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response defines cross-origin resource loading behaviour.",
    "interpretation_missing": "No Cross-Origin-Resource-Policy header was observed.",
    "recommendation_missing": "For sensitive resources, review whether CORP should be configured.",
    "recommendation_present": "Confirm the policy matches the intended resource sharing model.",
    "notes": "Contextual. Static public assets may intentionally allow cross-origin use."
}
```

## 9.10 Cross-Origin-Embedder-Policy

```python
{
    "canonical_name": "Cross-Origin-Embedder-Policy",
    "normalized_name": "cross-origin-embedder-policy",
    "category": "Security & Browser Protection",
    "purpose": "Controls whether a document can load cross-origin resources without explicit permission.",
    "expected": "contextual",
    "recommended_values": ["require-corp", "credentialless", "unsafe-none"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "Informational",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response defines cross-origin embedder behaviour.",
    "interpretation_missing": "No Cross-Origin-Embedder-Policy header was observed.",
    "recommendation_missing": "Only consider COEP where cross-origin isolation is required.",
    "recommendation_present": "Confirm that embedded resources support the selected policy.",
    "notes": "Do not score absence by default."
}
```

---

# 10. Caching & Freshness Headers

## 10.1 Cache-Control

```python
{
    "canonical_name": "Cache-Control",
    "normalized_name": "cache-control",
    "category": "Caching & Freshness",
    "purpose": "Defines caching directives for browsers and intermediary caches.",
    "expected": "present",
    "recommended_values": ["max-age", "no-cache", "no-store", "public", "private", "must-revalidate"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "Low",
    "score_if_missing": 1,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response includes cache behaviour instructions.",
    "interpretation_missing": "The response does not include Cache-Control.",
    "recommendation_missing": "Consider defining Cache-Control according to the content type and freshness requirements.",
    "recommendation_present": "Review whether the directives match the content's expected freshness and privacy requirements.",
    "notes": "Do not assume one cache policy fits all sites."
}
```

## 10.2 Expires

```python
{
    "canonical_name": "Expires",
    "normalized_name": "expires",
    "category": "Caching & Freshness",
    "purpose": "Provides an absolute expiry time for cached content.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": True,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response includes an absolute cache expiry value.",
    "interpretation_missing": "No Expires header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Cache-Control is usually preferred for modern cache control.",
    "notes": "Expires may coexist with Cache-Control."
}
```

## 10.3 ETag

```python
{
    "canonical_name": "ETag",
    "normalized_name": "etag",
    "category": "Caching & Freshness",
    "purpose": "Provides a validator that clients can use for conditional requests.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "Informational",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response includes an entity tag for cache validation.",
    "interpretation_missing": "No ETag header was observed.",
    "recommendation_missing": "ETags may improve cache validation for suitable resources.",
    "recommendation_present": "Confirm ETag behaviour is compatible with the hosting or CDN layer.",
    "notes": "Absence is not necessarily a problem."
}
```

## 10.4 Last-Modified

```python
{
    "canonical_name": "Last-Modified",
    "normalized_name": "last-modified",
    "category": "Caching & Freshness",
    "purpose": "Indicates when the origin believes the resource was last changed.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "Informational",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response includes a last modified timestamp.",
    "interpretation_missing": "No Last-Modified header was observed.",
    "recommendation_missing": "Last-Modified may help clients and caches validate unchanged content.",
    "recommendation_present": None,
    "notes": "Useful for static resources and cache validation."
}
```

## 10.5 Vary

```python
{
    "canonical_name": "Vary",
    "normalized_name": "vary",
    "category": "Caching & Freshness",
    "purpose": "Describes which request headers influence the selected response representation.",
    "expected": "contextual",
    "recommended_values": ["Accept-Encoding"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "Informational",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response tells caches which request headers affect the response variant.",
    "interpretation_missing": "No Vary header was observed.",
    "recommendation_missing": "If compression or content negotiation is used, review whether Vary is appropriate.",
    "recommendation_present": "Confirm the Vary value reflects actual content negotiation behaviour.",
    "notes": "Vary: Accept-Encoding is common with compressed responses."
}
```

## 10.6 Age

```python
{
    "canonical_name": "Age",
    "normalized_name": "age",
    "category": "Caching & Freshness",
    "purpose": "Indicates how long a response has been stored in a cache.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response appears to have passed through a cache that reports object age.",
    "interpretation_missing": "No Age header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Use together with cache headers to understand cache behaviour.",
    "notes": "Often seen with proxy or CDN caches."
}
```

---

# 11. Compression & Transfer Headers

## 11.1 Content-Encoding

```python
{
    "canonical_name": "Content-Encoding",
    "normalized_name": "content-encoding",
    "category": "Compression & Transfer",
    "purpose": "Describes compression or encoding applied to the response body.",
    "expected": "contextual",
    "recommended_values": ["br", "gzip", "deflate", "zstd"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "Low",
    "score_if_missing": 1,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response body appears to be compressed or encoded.",
    "interpretation_missing": "No Content-Encoding header was observed.",
    "recommendation_missing": "For compressible text-based content, consider enabling modern compression such as Brotli or gzip.",
    "recommendation_present": "Confirm compression is applied only to suitable content types.",
    "notes": "Absence may be acceptable for already-compressed assets."
}
```

## 11.2 Transfer-Encoding

```python
{
    "canonical_name": "Transfer-Encoding",
    "normalized_name": "transfer-encoding",
    "category": "Compression & Transfer",
    "purpose": "Describes transfer coding used to send the response body.",
    "expected": "optional",
    "recommended_values": ["chunked"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response uses transfer encoding such as chunked delivery.",
    "interpretation_missing": "No Transfer-Encoding header was observed.",
    "recommendation_missing": None,
    "recommendation_present": None,
    "notes": "Informational for this tool."
}
```

## 11.3 Content-Length

```python
{
    "canonical_name": "Content-Length",
    "normalized_name": "content-length",
    "category": "Compression & Transfer",
    "purpose": "Indicates the size of the response body in bytes when known.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response declares a content length.",
    "interpretation_missing": "No Content-Length header was observed.",
    "recommendation_missing": None,
    "recommendation_present": None,
    "notes": "May be absent with chunked transfer or dynamic responses."
}
```

## 11.4 Accept-Ranges

```python
{
    "canonical_name": "Accept-Ranges",
    "normalized_name": "accept-ranges",
    "category": "Compression & Transfer",
    "purpose": "Indicates whether the server supports range requests for partial content retrieval.",
    "expected": "optional",
    "recommended_values": ["bytes", "none"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response indicates whether partial content requests are supported.",
    "interpretation_missing": "No Accept-Ranges header was observed.",
    "recommendation_missing": None,
    "recommendation_present": None,
    "notes": "Useful for large static files but not required for all pages."
}
```

---

# 12. Content Metadata Headers

## 12.1 Content-Type

```python
{
    "canonical_name": "Content-Type",
    "normalized_name": "content-type",
    "category": "Content Metadata",
    "purpose": "Describes the media type and optional character encoding of the response body.",
    "expected": "present",
    "recommended_values": ["text/html; charset=UTF-8"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "Medium",
    "score_if_missing": 2,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response declares its content type.",
    "interpretation_missing": "The response does not declare a Content-Type.",
    "recommendation_missing": "Configure the server or application to return an appropriate Content-Type for the response.",
    "recommendation_present": "Confirm the declared type matches the actual response content.",
    "notes": "Content-Type is foundational response metadata."
}
```

## 12.2 Content-Language

```python
{
    "canonical_name": "Content-Language",
    "normalized_name": "content-language",
    "category": "Content Metadata",
    "purpose": "Describes the intended language audience for the response.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response declares a content language.",
    "interpretation_missing": "No Content-Language header was observed.",
    "recommendation_missing": None,
    "recommendation_present": None,
    "notes": "May be useful for multilingual websites."
}
```

## 12.3 Content-Location

```python
{
    "canonical_name": "Content-Location",
    "normalized_name": "content-location",
    "category": "Content Metadata",
    "purpose": "Identifies an alternate location for the returned representation.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response identifies a content location for the representation.",
    "interpretation_missing": "No Content-Location header was observed.",
    "recommendation_missing": None,
    "recommendation_present": None,
    "notes": "Rare on normal homepages."
}
```

## 12.4 Digest

```python
{
    "canonical_name": "Digest",
    "normalized_name": "digest",
    "category": "Content Metadata",
    "purpose": "Provides a digest of the response content.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response includes a content digest.",
    "interpretation_missing": "No Digest header was observed.",
    "recommendation_missing": None,
    "recommendation_present": None,
    "notes": "Informational for v1.2."
}
```

---

# 13. Cookies & Sessions Headers

## 13.1 Set-Cookie

```python
{
    "canonical_name": "Set-Cookie",
    "normalized_name": "set-cookie",
    "category": "Cookies & Sessions",
    "purpose": "Instructs the browser to store a cookie.",
    "expected": "contextual",
    "recommended_values": ["Secure", "HttpOnly", "SameSite"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response sets one or more cookies.",
    "interpretation_missing": "No Set-Cookie header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Review cookie attributes such as Secure, HttpOnly, and SameSite where cookies are used for sessions or sensitive workflows.",
    "notes": "Cookie attribute analysis must happen in the cookie collector."
}
```

Cookie attribute scoring:

```text
Cookie present without Secure: Medium, score 2
Cookie present without HttpOnly: Medium, score 2
Cookie present without SameSite: Low, score 1
Cookie present with all three: Informational, score 0
No cookies present: Informational, score 0
```

---

# 14. Redirect & Location Headers

## 14.1 Location

```python
{
    "canonical_name": "Location",
    "normalized_name": "location",
    "category": "Redirect & Location",
    "purpose": "Identifies the target URL for a redirect or newly created resource.",
    "expected": "contextual",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response includes a Location header, usually associated with redirect behaviour.",
    "interpretation_missing": "No Location header was observed in the final response.",
    "recommendation_missing": None,
    "recommendation_present": "Review redirect behaviour in the connectivity section.",
    "notes": "Final responses may not include Location unless they are redirect responses."
}
```

## 14.2 Refresh

```python
{
    "canonical_name": "Refresh",
    "normalized_name": "refresh",
    "category": "Redirect & Location",
    "purpose": "Requests client-side refresh or redirect after a delay.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": True,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Low",
    "score_if_present": 1,
    "interpretation_present": "The response includes a Refresh header, which may indicate client-side redirect or reload behaviour.",
    "interpretation_missing": "No Refresh header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Review whether HTTP redirects would be clearer and more predictable than Refresh-based behaviour.",
    "notes": "Treat as low operational advisory if present."
}
```

---

# 15. CORS & Cross-Origin Access Headers

CORS headers are contextual.

They should be reported, but they should not be aggressively scored on normal homepage responses.

## 15.1 Access-Control-Allow-Origin

```python
{
    "canonical_name": "Access-Control-Allow-Origin",
    "normalized_name": "access-control-allow-origin",
    "category": "CORS & Cross-Origin Access",
    "purpose": "Indicates which origins may access the response through browser CORS rules.",
    "expected": "contextual",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response defines a CORS origin policy.",
    "interpretation_missing": "No Access-Control-Allow-Origin header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Confirm that the allowed origin value matches the intended API or resource sharing model.",
    "notes": "If value is * and credentials are also allowed, create a Medium finding."
}
```

Special rule:

```text
Access-Control-Allow-Origin: *
AND
Access-Control-Allow-Credentials: true

Risk: Medium
Score: 2
Recommendation: Review CORS policy because wildcard origins should not be combined with credentialed access.
```

## 15.2 Access-Control-Allow-Credentials

```python
{
    "canonical_name": "Access-Control-Allow-Credentials",
    "normalized_name": "access-control-allow-credentials",
    "category": "CORS & Cross-Origin Access",
    "purpose": "Indicates whether browsers may expose responses to frontend code when credentials are included.",
    "expected": "contextual",
    "recommended_values": ["true"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response indicates whether credentialed CORS access is allowed.",
    "interpretation_missing": "No Access-Control-Allow-Credentials header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Confirm that credentialed cross-origin access is intentional.",
    "notes": "Only concerning when combined with overly broad origins."
}
```

## 15.3 Access-Control-Allow-Methods

```python
{
    "canonical_name": "Access-Control-Allow-Methods",
    "normalized_name": "access-control-allow-methods",
    "category": "CORS & Cross-Origin Access",
    "purpose": "Lists HTTP methods allowed for CORS requests.",
    "expected": "contextual",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response lists methods allowed for cross-origin requests.",
    "interpretation_missing": "No Access-Control-Allow-Methods header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Confirm the allowed methods match the intended cross-origin interface.",
    "notes": "Usually relevant to APIs and preflight responses."
}
```

## 15.4 Access-Control-Allow-Headers

```python
{
    "canonical_name": "Access-Control-Allow-Headers",
    "normalized_name": "access-control-allow-headers",
    "category": "CORS & Cross-Origin Access",
    "purpose": "Lists request headers allowed for CORS requests.",
    "expected": "contextual",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response lists request headers allowed for cross-origin requests.",
    "interpretation_missing": "No Access-Control-Allow-Headers header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Confirm allowed headers are limited to what the application requires.",
    "notes": "Contextual."
}
```

## 15.5 Access-Control-Expose-Headers

```python
{
    "canonical_name": "Access-Control-Expose-Headers",
    "normalized_name": "access-control-expose-headers",
    "category": "CORS & Cross-Origin Access",
    "purpose": "Lists response headers exposed to browser frontend code during CORS requests.",
    "expected": "contextual",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response exposes selected headers to cross-origin browser code.",
    "interpretation_missing": "No Access-Control-Expose-Headers header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Confirm exposed headers are intentional.",
    "notes": "Contextual."
}
```

## 15.6 Access-Control-Max-Age

```python
{
    "canonical_name": "Access-Control-Max-Age",
    "normalized_name": "access-control-max-age",
    "category": "CORS & Cross-Origin Access",
    "purpose": "Defines how long browsers may cache CORS preflight results.",
    "expected": "contextual",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response defines how long CORS preflight results may be cached.",
    "interpretation_missing": "No Access-Control-Max-Age header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Confirm the duration matches the expected API change rate.",
    "notes": "Usually relevant to API endpoints."
}
```

---

# 16. CDN / Proxy / Edge Infrastructure Headers

These headers are infrastructure hints.

They should usually be informational.

## 16.1 CF-Ray

```python
{
    "canonical_name": "CF-Ray",
    "normalized_name": "cf-ray",
    "category": "CDN / Proxy / Edge Infrastructure",
    "purpose": "Cloudflare request identifier header.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "Cloudflare edge infrastructure indicators were observed.",
    "interpretation_missing": "No CF-Ray header was observed.",
    "recommendation_missing": None,
    "recommendation_present": None,
    "notes": "Use cautious wording: Cloudflare indicators observed."
}
```

## 16.2 CF-Cache-Status

```python
{
    "canonical_name": "CF-Cache-Status",
    "normalized_name": "cf-cache-status",
    "category": "CDN / Proxy / Edge Infrastructure",
    "purpose": "Indicates Cloudflare cache handling for the response.",
    "expected": "optional",
    "recommended_values": ["HIT", "MISS", "DYNAMIC", "BYPASS", "EXPIRED", "REVALIDATED"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "Cloudflare cache status information was observed.",
    "interpretation_missing": "No CF-Cache-Status header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Review cache status together with Cache-Control for CDN behaviour.",
    "notes": "Informational."
}
```

## 16.3 X-Cache

```python
{
    "canonical_name": "X-Cache",
    "normalized_name": "x-cache",
    "category": "CDN / Proxy / Edge Infrastructure",
    "purpose": "Common non-standard cache status indicator used by proxies and CDNs.",
    "expected": "optional",
    "recommended_values": ["HIT", "MISS", "BYPASS"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "A cache layer appears to report cache handling status.",
    "interpretation_missing": "No X-Cache header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Use this as an infrastructure hint rather than a standalone performance conclusion.",
    "notes": "Non-standard but common."
}
```

## 16.4 X-Served-By

```python
{
    "canonical_name": "X-Served-By",
    "normalized_name": "x-served-by",
    "category": "CDN / Proxy / Edge Infrastructure",
    "purpose": "Often identifies a serving cache node, edge node, or backend layer.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response includes an infrastructure serving hint.",
    "interpretation_missing": "No X-Served-By header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Consider whether exposed node identifiers are useful for operations or should be minimized.",
    "notes": "Usually informational."
}
```

## 16.5 Via

```python
{
    "canonical_name": "Via",
    "normalized_name": "via",
    "category": "CDN / Proxy / Edge Infrastructure",
    "purpose": "Indicates intermediate proxies through which the message passed.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response indicates that an intermediary may have handled the request.",
    "interpretation_missing": "No Via header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Review whether intermediary disclosure is expected.",
    "notes": "Informational."
}
```

## 16.6 X-Backend-Server

```python
{
    "canonical_name": "X-Backend-Server",
    "normalized_name": "x-backend-server",
    "category": "CDN / Proxy / Edge Infrastructure",
    "purpose": "Non-standard header sometimes used to identify a backend server.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Low",
    "score_if_present": 1,
    "interpretation_present": "The response may expose backend server identity information.",
    "interpretation_missing": "No X-Backend-Server header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Consider whether backend identifiers need to be exposed publicly.",
    "notes": "Low advisory only."
}
```

---

# 17. Server / Application Disclosure Headers

## 17.1 Server

```python
{
    "canonical_name": "Server",
    "normalized_name": "server",
    "category": "Server / Application Disclosure",
    "purpose": "Identifies server software or infrastructure handling the response.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Low",
    "score_if_present": 1,
    "interpretation_present": "The response discloses server software or infrastructure information.",
    "interpretation_missing": "No Server header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Consider minimizing detailed version disclosure where practical.",
    "notes": "Presence is common. Do not overstate risk."
}
```

## 17.2 X-Powered-By

```python
{
    "canonical_name": "X-Powered-By",
    "normalized_name": "x-powered-by",
    "category": "Server / Application Disclosure",
    "purpose": "Non-standard header commonly used to disclose application framework or runtime information.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Low",
    "score_if_present": 1,
    "interpretation_present": "The response discloses application runtime or framework information.",
    "interpretation_missing": "No X-Powered-By header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Consider suppressing unnecessary application technology disclosure.",
    "notes": "Low advisory only."
}
```

## 17.3 X-AspNet-Version

```python
{
    "canonical_name": "X-AspNet-Version",
    "normalized_name": "x-aspnet-version",
    "category": "Server / Application Disclosure",
    "purpose": "Non-standard header that may disclose ASP.NET version information.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": True,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Low",
    "score_if_present": 1,
    "interpretation_present": "The response may disclose ASP.NET version information.",
    "interpretation_missing": "No X-AspNet-Version header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Consider suppressing detailed framework version disclosure.",
    "notes": "Low advisory."
}
```

## 17.4 X-Generator

```python
{
    "canonical_name": "X-Generator",
    "normalized_name": "x-generator",
    "category": "Server / Application Disclosure",
    "purpose": "May identify the application or generator used to produce the response.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Low",
    "score_if_present": 1,
    "interpretation_present": "The response discloses generator or application information.",
    "interpretation_missing": "No X-Generator header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Consider whether generator disclosure is useful or should be minimized.",
    "notes": "Low advisory."
}
```

---

# 18. Protocol / Connection Behaviour Headers

## 18.1 Connection

```python
{
    "canonical_name": "Connection",
    "normalized_name": "connection",
    "category": "Protocol / Connection Behaviour",
    "purpose": "Controls connection management behaviour for the current connection.",
    "expected": "optional",
    "recommended_values": ["keep-alive", "close"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response includes connection management information.",
    "interpretation_missing": "No Connection header was observed.",
    "recommendation_missing": None,
    "recommendation_present": None,
    "notes": "Informational."
}
```

## 18.2 Keep-Alive

```python
{
    "canonical_name": "Keep-Alive",
    "normalized_name": "keep-alive",
    "category": "Protocol / Connection Behaviour",
    "purpose": "Provides connection persistence parameters.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": True,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response includes keep-alive connection parameters.",
    "interpretation_missing": "No Keep-Alive header was observed.",
    "recommendation_missing": None,
    "recommendation_present": None,
    "notes": "Usually informational."
}
```

## 18.3 Alt-Svc

```python
{
    "canonical_name": "Alt-Svc",
    "normalized_name": "alt-svc",
    "category": "Protocol / Connection Behaviour",
    "purpose": "Advertises alternative services such as HTTP/3 availability.",
    "expected": "optional",
    "recommended_values": ["h3"],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response advertises alternative protocol or service options.",
    "interpretation_missing": "No Alt-Svc header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Use as a protocol capability hint, not a complete HTTP/3 verification.",
    "notes": "Do not claim HTTP/3 support solely from Alt-Svc without cautious wording."
}
```

## 18.4 Upgrade

```python
{
    "canonical_name": "Upgrade",
    "normalized_name": "upgrade",
    "category": "Protocol / Connection Behaviour",
    "purpose": "Advertises a protocol upgrade option.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response advertises a possible protocol upgrade.",
    "interpretation_missing": "No Upgrade header was observed.",
    "recommendation_missing": None,
    "recommendation_present": None,
    "notes": "Informational."
}
```

---

# 19. Reporting & Monitoring Headers

## 19.1 Report-To

```python
{
    "canonical_name": "Report-To",
    "normalized_name": "report-to",
    "category": "Reporting & Monitoring",
    "purpose": "Defines reporting endpoints for browser-generated reports.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response defines browser reporting endpoint configuration.",
    "interpretation_missing": "No Report-To header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Confirm report endpoints are actively monitored if configured.",
    "notes": "Informational."
}
```

## 19.2 Reporting-Endpoints

```python
{
    "canonical_name": "Reporting-Endpoints",
    "normalized_name": "reporting-endpoints",
    "category": "Reporting & Monitoring",
    "purpose": "Defines named endpoints for browser reporting.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response defines browser reporting endpoints.",
    "interpretation_missing": "No Reporting-Endpoints header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Confirm reporting endpoints are expected and monitored.",
    "notes": "Informational."
}
```

## 19.3 NEL

```python
{
    "canonical_name": "NEL",
    "normalized_name": "nel",
    "category": "Reporting & Monitoring",
    "purpose": "Configures Network Error Logging for browsers.",
    "expected": "optional",
    "recommended_values": [],
    "deprecated": False,
    "legacy": False,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "The response includes Network Error Logging configuration.",
    "interpretation_missing": "No NEL header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Confirm that network error reports are useful and monitored.",
    "notes": "Informational."
}
```

---

# 20. Legacy / Deprecated Headers

Legacy or deprecated headers should be detected and explained.

They should not be rewarded as modern protection.

## 20.1 X-XSS-Protection

```python
{
    "canonical_name": "X-XSS-Protection",
    "normalized_name": "x-xss-protection",
    "category": "Legacy / Deprecated Headers",
    "purpose": "Legacy browser XSS filter control header.",
    "expected": "legacy",
    "recommended_values": ["0"],
    "deprecated": True,
    "legacy": True,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "A legacy X-XSS-Protection header was observed.",
    "interpretation_missing": "No X-XSS-Protection header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Do not rely on this legacy header as a modern protection mechanism. Prefer a well-designed Content-Security-Policy.",
    "notes": "Presence should be reported as legacy, not as a security improvement."
}
```

## 20.2 Public-Key-Pins

```python
{
    "canonical_name": "Public-Key-Pins",
    "normalized_name": "public-key-pins",
    "category": "Legacy / Deprecated Headers",
    "purpose": "Legacy HTTP Public Key Pinning configuration.",
    "expected": "deprecated",
    "recommended_values": [],
    "deprecated": True,
    "legacy": True,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Low",
    "score_if_present": 1,
    "interpretation_present": "A deprecated Public-Key-Pins header was observed.",
    "interpretation_missing": "No Public-Key-Pins header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Review and remove HPKP configuration unless there is a specific legacy reason for its presence.",
    "notes": "Deprecated and potentially operationally risky if misconfigured."
}
```

## 20.3 Public-Key-Pins-Report-Only

```python
{
    "canonical_name": "Public-Key-Pins-Report-Only",
    "normalized_name": "public-key-pins-report-only",
    "category": "Legacy / Deprecated Headers",
    "purpose": "Legacy report-only HPKP configuration.",
    "expected": "deprecated",
    "recommended_values": [],
    "deprecated": True,
    "legacy": True,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Low",
    "score_if_present": 1,
    "interpretation_present": "A deprecated HPKP report-only header was observed.",
    "interpretation_missing": "No Public-Key-Pins-Report-Only header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Review whether this legacy reporting configuration is still required.",
    "notes": "Legacy."
}
```

## 20.4 Expect-CT

```python
{
    "canonical_name": "Expect-CT",
    "normalized_name": "expect-ct",
    "category": "Legacy / Deprecated Headers",
    "purpose": "Previously used to opt into Certificate Transparency enforcement or reporting.",
    "expected": "deprecated",
    "recommended_values": [],
    "deprecated": True,
    "legacy": True,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "An Expect-CT header was observed, but this is now legacy behaviour.",
    "interpretation_missing": "No Expect-CT header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Review whether this legacy header is still needed.",
    "notes": "Do not recommend adding this header."
}
```

## 20.5 Feature-Policy

```python
{
    "canonical_name": "Feature-Policy",
    "normalized_name": "feature-policy",
    "category": "Legacy / Deprecated Headers",
    "purpose": "Legacy predecessor to Permissions-Policy.",
    "expected": "deprecated",
    "recommended_values": [],
    "deprecated": True,
    "legacy": True,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "A legacy Feature-Policy header was observed.",
    "interpretation_missing": "No Feature-Policy header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Consider migrating relevant policy settings to Permissions-Policy.",
    "notes": "Do not treat as modern replacement for Permissions-Policy."
}
```

## 20.6 Pragma

```python
{
    "canonical_name": "Pragma",
    "normalized_name": "pragma",
    "category": "Legacy / Deprecated Headers",
    "purpose": "Legacy HTTP/1.0 cache control header.",
    "expected": "legacy",
    "recommended_values": ["no-cache"],
    "deprecated": False,
    "legacy": True,
    "risk_if_missing": "None",
    "score_if_missing": 0,
    "risk_if_present": "Informational",
    "score_if_present": 0,
    "interpretation_present": "A legacy cache-control header was observed.",
    "interpretation_missing": "No Pragma header was observed.",
    "recommendation_missing": None,
    "recommendation_present": "Use Cache-Control as the primary modern cache directive.",
    "notes": "Common with no-cache responses."
}
```

---

# 21. Additional Known Headers to Classify

The following headers must be recognized and categorized when observed, even if v1.2 does not deeply interpret them.

## Content Metadata

```text
Content-Disposition
Content-Range
Content-Digest
Repr-Digest
Want-Content-Digest
Link
Allow
Accept-Patch
Accept-Post
```

## Caching & Freshness

```text
Surrogate-Control
CDN-Cache-Control
Clear-Site-Data
```

## Compression & Transfer

```text
Trailer
TE
```

## Protocol / Connection Behaviour

```text
Date
Early-Data
Retry-After
Upgrade-Insecure-Requests
```

## Redirect & Location

```text
Link
```

## Server / Application Disclosure

```text
X-Runtime
X-Request-ID
X-Correlation-ID
X-Amzn-Trace-Id
```

## CDN / Proxy / Edge Infrastructure

```text
Fastly-Debug-Digest
X-Fastly-Request-ID
X-Akamai-Transformed
X-CDN
X-Proxy-Cache
X-Cache-Hits
X-Timer
Fly-Request-Id
Render-Origin-Server
Vercel-Cache
X-Vercel-Id
X-Netlify-Cache
X-Platform
```

## Reporting & Monitoring

```text
Server-Timing
Timing-Allow-Origin
```

## CORS & Cross-Origin Access

```text
Cross-Origin-Resource-Policy
Cross-Origin-Opener-Policy
Cross-Origin-Embedder-Policy
Origin-Agent-Cluster
```

---

# 22. Missing Header Expectations

Site Inspector should distinguish between:

```text
headers expected for most public websites
headers useful but contextual
headers optional
headers legacy
headers deprecated
```

Expected for most public HTML websites:

```text
Content-Type
Strict-Transport-Security
Content-Security-Policy
X-Content-Type-Options
X-Frame-Options or CSP frame-ancestors
Referrer-Policy
Cache-Control
```

Useful but contextual:

```text
Permissions-Policy
Cross-Origin-Opener-Policy
Cross-Origin-Resource-Policy
Cross-Origin-Embedder-Policy
ETag
Last-Modified
Vary
Content-Encoding
Set-Cookie
CORS headers
Alt-Svc
Report-To
NEL
```

Optional / informational:

```text
Server
Via
Age
Accept-Ranges
Server-Timing
Timing-Allow-Origin
```

Legacy / deprecated:

```text
X-XSS-Protection
Public-Key-Pins
Expect-CT
Feature-Policy
Pragma
```

---

# 23. Header Finding Generation Rules

A header should generate a finding when one of these is true:

```text
A recommended known header is missing.
A known header is present but uses an unexpected value.
A deprecated header is present.
A disclosure header exposes detailed server or framework information.
A risky combination is observed.
A cookie-related header sets cookies without expected attributes.
```

A header should not generate a risk finding when:

```text
It is optional and absent.
It is unknown.
It is vendor-specific.
It is purely informational.
It is contextual and no risky combination is observed.
```

---

# 24. Risky Header Combinations

Version 1.2 should support combination-based findings.

## 24.1 CORS wildcard with credentials

Condition:

```text
Access-Control-Allow-Origin: *
Access-Control-Allow-Credentials: true
```

Finding:

```text
Credentialed CORS access appears broadly allowed.
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
Review whether credentialed cross-origin access should be limited to specific trusted origins.
```

## 24.2 Cookies without Secure over HTTPS

Condition:

```text
Final URL uses HTTPS
Set-Cookie present
Cookie lacks Secure
```

Finding:

```text
Cookie set without Secure attribute.
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

## 24.3 Cookies without HttpOnly

Condition:

```text
Set-Cookie present
Cookie lacks HttpOnly
```

Finding:

```text
Cookie set without HttpOnly attribute.
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

## 24.4 CSP present but overly broad

Condition examples:

```text
Content-Security-Policy includes unsafe-inline
Content-Security-Policy includes unsafe-eval
Content-Security-Policy includes default-src *
```

Risk:

```text
Low or Medium depending on rule
```

v1.2 guidance:

Do not overbuild CSP analysis immediately.

Only flag clearly broad patterns with careful wording.

---

# 25. Report Requirements for Headers

The report must show headers hierarchically.

Required header report structure:

```text
Header Overview
    Total Observed
    Known Observed
    Unknown Observed
    Expected Known Missing
    Deprecated Observed

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

Each header entry should show:

```text
Header Name
Observed Value
Status
Interpretation
Recommendation
Risk Contribution
```

Unknown headers should show:

```text
Header Name
Observed Value
Category: Vendor-Specific / Unclassified
Interpretation: Header observed but not classified by Site Inspector.
```

---

# 26. JSON Requirements for Headers

JSON output must include:

```python
{
    "headers": {
        "raw": {},
        "normalized": {},
        "categorized": {},
        "summary": {}
    }
}
```

Each categorized header object must include:

```text
name
normalized_name
value
present
known
category
deprecated
legacy
purpose
interpretation
recommendation
risk_contribution
score
```

---

# 27. Implementation Priority for Volume IV

Codex should implement header intelligence in phases.

## Phase 1

Collect all headers and preserve raw output.

## Phase 2

Normalize header names.

## Phase 3

Introduce category buckets.

## Phase 4

Create header knowledge base dictionary.

## Phase 5

Categorize observed headers.

## Phase 6

Add expected-known missing headers.

## Phase 7

Generate findings from header knowledge base.

## Phase 8

Add combination rules.

## Phase 9

Update report output.

---

# 28. Success Criteria for Volume IV

The header knowledge base is successful if:

```text
Every observed header is preserved.
Every observed known header is categorized correctly.
Every observed unknown header is shown as Vendor-Specific / Unclassified.
Known missing headers are reported separately from observed headers.
Legacy headers are detected and explained.
Deprecated headers are not treated as modern protections.
Header findings are traceable to evidence.
Risk scoring remains conservative.
The report gives users the full picture without overwhelming them with unsupported warnings.
```

---

# 29. Final Header Rule

Site Inspector must not decide that a header is unimportant simply because the current implementation does not understand it.

The tool must preserve it, categorize it when possible, explain it when known, and expose it when unknown.

Classification can improve over time.

Discarded evidence cannot.
