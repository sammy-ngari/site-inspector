"""
Deterministic header categories and metadata definitions for Site Inspector.
"""

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
    "vendor_specific_unclassified": "Vendor-Specific / Unclassified",
}

RISK_SCORES = {
    "Informational": 0,
    "Low": 1,
    "Medium": 2,
    "High": 3,
    None: 0,
}


def _score_for_risk(level):
    """
    Convert a risk label into the conservative score used by the knowledge base.
    """

    return RISK_SCORES.get(level, 0)


def _default_present_recommendation(category_name, deprecated):
    """
    Provide conservative default wording for observed known headers.
    """

    if deprecated:
        return (
            "Review whether a modern replacement should be used instead of "
            "this legacy or deprecated header."
        )

    recommendations = {
        "Security & Browser Protection": (
            "Confirm that the observed browser protection behavior matches "
            "the site's intended delivery model."
        ),
        "Caching & Freshness": (
            "Review whether the observed cache directives match the content's "
            "expected freshness and privacy requirements."
        ),
        "Compression & Transfer": (
            "Review whether the observed transfer behavior matches the site's "
            "performance and delivery requirements."
        ),
        "Content Metadata": (
            "Review whether the observed metadata matches the content's "
            "intended behavior."
        ),
        "Cookies & Sessions": (
            "Review whether the observed cookie behavior matches the site's "
            "session requirements."
        ),
        "Redirect & Location": (
            "Confirm that the observed redirect or location behavior is intentional."
        ),
        "CORS & Cross-Origin Access": (
            "Review whether the observed cross-origin behavior matches the "
            "site's intended access model."
        ),
        "CDN / Proxy / Edge Infrastructure": (
            "If this infrastructure disclosure is intentional, no action may be required."
        ),
        "Server / Application Disclosure": (
            "If this technology disclosure is intentional, no action may be required."
        ),
        "Protocol / Connection Behaviour": (
            "Confirm that the observed protocol behavior matches the site's "
            "delivery requirements."
        ),
        "Reporting & Monitoring": (
            "Review whether the observed monitoring or reporting behavior is intentional."
        ),
    }
    return recommendations.get(category_name)


def _build_header_metadata(
    canonical_name,
    category_name,
    purpose,
    expected="optional",
    deprecated=False,
    legacy=False,
    interpretation_present=None,
    interpretation_missing=None,
    recommendation_present=None,
    recommendation_missing=None,
    recommended_values=None,
    risk_if_present="Informational",
    risk_if_missing="Informational",
    notes="",
):
    """
    Build a schema-aligned header metadata entry.
    """

    normalized_name = canonical_name.lower()

    if interpretation_present is None:
        interpretation_present = f"The response includes the {canonical_name} header."

    if interpretation_missing is None:
        interpretation_missing = f"The response does not include the {canonical_name} header."

    if recommendation_present is None:
        recommendation_present = _default_present_recommendation(category_name, deprecated)

    if recommendation_missing is None and expected == "present":
        recommendation_missing = (
            f"Consider defining the {canonical_name} header if the site's "
            "intended behavior should be communicated explicitly."
        )

    if recommended_values is None:
        recommended_values = []

    return {
        "canonical_name": canonical_name,
        "normalized_name": normalized_name,
        "category": category_name,
        "purpose": purpose,
        "expected": expected,
        "recommended_values": recommended_values,
        "deprecated": deprecated,
        "legacy": legacy,
        "risk_if_missing": risk_if_missing,
        "score_if_missing": _score_for_risk(risk_if_missing),
        "risk_if_present": risk_if_present,
        "score_if_present": _score_for_risk(risk_if_present),
        "interpretation_present": interpretation_present,
        "interpretation_missing": interpretation_missing,
        "recommendation_missing": recommendation_missing,
        "recommendation_present": recommendation_present,
        "notes": notes,
    }


def _build_header_knowledge_base():
    """
    Create the deterministic Phase 4 header knowledge base.
    """

    knowledge_base = {}

    def register(canonical_name, category_key, purpose, **kwargs):
        knowledge_base[canonical_name.lower()] = _build_header_metadata(
            canonical_name,
            HEADER_CATEGORIES[category_key],
            purpose,
            **kwargs,
        )

    register(
        "Strict-Transport-Security",
        "security_browser_protection",
        "Instructs browsers to prefer HTTPS for future requests.",
        expected="present",
        interpretation_present="The response includes an HSTS policy for future browser requests.",
        interpretation_missing="The response does not include an HSTS policy for future browser requests.",
        recommendation_missing=(
            "Consider enabling Strict-Transport-Security after confirming that "
            "all intended content is served securely over HTTPS."
        ),
        risk_if_missing="Medium",
        notes="Expected for most public HTML websites served over HTTPS.",
    )
    register(
        "Content-Security-Policy",
        "security_browser_protection",
        "Defines browser-enforced restrictions for permitted content sources.",
        expected="present",
        interpretation_present="The response includes a site-defined content security policy.",
        interpretation_missing="The response does not include a site-defined content security policy.",
        recommendation_missing=(
            "Consider defining a Content-Security-Policy appropriate to the "
            "application and testing it in report-only mode where practical."
        ),
        risk_if_missing="Medium",
        notes="Expected for most public HTML websites.",
    )
    register(
        "Content-Security-Policy-Report-Only",
        "security_browser_protection",
        "Allows CSP policy testing without enforcement.",
        expected="contextual",
        notes="Useful for staged CSP rollout and policy testing.",
    )
    register(
        "X-Content-Type-Options",
        "security_browser_protection",
        "Instructs browsers not to guess content types beyond the declared value.",
        expected="present",
        recommended_values=["nosniff"],
        interpretation_missing="The response does not include browser guidance for strict content type handling.",
        recommendation_missing=(
            "Consider setting X-Content-Type-Options if strict browser content "
            "type handling is intended."
        ),
        risk_if_missing="Medium",
        notes="Expected for most public HTML websites.",
    )
    register(
        "X-Frame-Options",
        "security_browser_protection",
        "Communicates framing restrictions to browsers.",
        expected="present",
        recommended_values=["DENY", "SAMEORIGIN"],
        interpretation_missing="The response does not include an explicit X-Frame-Options policy.",
        recommendation_missing=(
            "Consider defining X-Frame-Options or confirming that equivalent "
            "framing restrictions are intentionally provided through Content-Security-Policy."
        ),
        risk_if_missing="Medium",
        notes="Expected unless equivalent frame-ancestors guidance is intentionally used.",
    )
    register(
        "Referrer-Policy",
        "security_browser_protection",
        "Controls how much referrer information browsers share on outbound requests.",
        expected="present",
        interpretation_missing="The response does not include an explicit referrer-sharing policy.",
        recommendation_missing=(
            "Consider defining a Referrer-Policy appropriate to the site's "
            "privacy, analytics, and application requirements."
        ),
        risk_if_missing="Low",
        notes="Expected for most public HTML websites.",
    )
    register(
        "Permissions-Policy",
        "security_browser_protection",
        "Communicates browser feature access preferences.",
        expected="contextual",
        notes="Useful but contextual depending on application features.",
    )
    register(
        "Cross-Origin-Opener-Policy",
        "security_browser_protection",
        "Communicates opener isolation behavior to browsers.",
        expected="contextual",
        notes="Cross-origin isolation controls are contextual.",
    )
    register(
        "Cross-Origin-Resource-Policy",
        "security_browser_protection",
        "Communicates resource-sharing restrictions for browser fetches.",
        expected="contextual",
        notes="Cross-origin resource sharing controls are contextual.",
    )
    register(
        "Cross-Origin-Embedder-Policy",
        "security_browser_protection",
        "Communicates embedding isolation requirements to browsers.",
        expected="contextual",
        notes="Cross-origin embedding controls are contextual.",
    )

    for canonical_name, purpose, expected, risk_if_missing, notes in (
        (
            "Cache-Control",
            "Defines cache behavior for browsers and intermediaries.",
            "present",
            "Low",
            "Expected for most public HTML websites.",
        ),
        (
            "Expires",
            "Provides an absolute cache expiry time.",
            "optional",
            "Informational",
            "Optional cache metadata.",
        ),
        (
            "ETag",
            "Provides an entity tag for cache revalidation.",
            "contextual",
            "Informational",
            "Useful but contextual for cache validation.",
        ),
        (
            "Last-Modified",
            "Provides a modification timestamp for cache revalidation.",
            "contextual",
            "Informational",
            "Useful but contextual for cache validation.",
        ),
        (
            "Vary",
            "Signals which request headers influence cached responses.",
            "contextual",
            "Informational",
            "Useful when response variants depend on request headers.",
        ),
        (
            "Age",
            "Reports the apparent age of a cached response.",
            "optional",
            "Informational",
            "Informational cache metadata.",
        ),
        (
            "Surrogate-Control",
            "Defines intermediary cache behavior.",
            "contextual",
            "Informational",
            "Contextual intermediary cache metadata.",
        ),
        (
            "CDN-Cache-Control",
            "Defines CDN-specific cache behavior.",
            "contextual",
            "Informational",
            "Contextual CDN cache metadata.",
        ),
        (
            "Clear-Site-Data",
            "Requests that supporting browsers clear selected local site data.",
            "contextual",
            "Informational",
            "Contextual browser data-clearing instruction.",
        ),
    ):
        register(
            canonical_name,
            "caching_freshness",
            purpose,
            expected=expected,
            interpretation_present=(
                f"The response includes the {canonical_name} header with cache-related guidance."
            ),
            risk_if_missing=risk_if_missing,
            recommendation_missing=(
                "Consider defining Cache-Control directives appropriate to the "
                "content's freshness and privacy requirements."
                if canonical_name == "Cache-Control"
                else None
            ),
            notes=notes,
        )

    for canonical_name, purpose, expected, notes in (
        (
            "Content-Encoding",
            "Indicates the encoding applied to the response body.",
            "contextual",
            "Useful but contextual depending on response size and delivery behavior.",
        ),
        (
            "Transfer-Encoding",
            "Indicates the transfer coding used for the response.",
            "optional",
            "Protocol-level transfer metadata.",
        ),
        (
            "Content-Length",
            "Indicates the declared response body length.",
            "optional",
            "Optional transfer metadata.",
        ),
        (
            "Accept-Ranges",
            "Indicates whether range requests are supported.",
            "optional",
            "Optional transfer metadata.",
        ),
        (
            "Trailer",
            "Indicates which trailer fields may appear after the message body.",
            "optional",
            "Optional transfer metadata.",
        ),
        (
            "TE",
            "Indicates accepted transfer codings in protocol negotiation.",
            "optional",
            "Optional protocol metadata.",
        ),
    ):
        register(
            canonical_name,
            "compression_transfer",
            purpose,
            expected=expected,
            notes=notes,
        )

    for canonical_name, purpose, expected, risk_if_missing, notes in (
        (
            "Content-Type",
            "Identifies the media type of the response body.",
            "present",
            "Low",
            "Expected for most public HTML websites.",
        ),
        (
            "Content-Language",
            "Indicates the natural language of the representation.",
            "optional",
            "Informational",
            "Optional content metadata.",
        ),
        (
            "Content-Location",
            "Indicates an alternate location for the representation.",
            "optional",
            "Informational",
            "Optional content metadata.",
        ),
        (
            "Digest",
            "Carries a representation digest.",
            "optional",
            "Informational",
            "Optional integrity metadata.",
        ),
        (
            "Content-Digest",
            "Carries a content digest for the representation.",
            "optional",
            "Informational",
            "Optional integrity metadata.",
        ),
        (
            "Repr-Digest",
            "Carries a representation digest value.",
            "optional",
            "Informational",
            "Optional integrity metadata.",
        ),
        (
            "Want-Content-Digest",
            "Expresses preference for content digest values.",
            "optional",
            "Informational",
            "Optional integrity preference metadata.",
        ),
        (
            "Content-Disposition",
            "Communicates handling or download behavior for content.",
            "optional",
            "Informational",
            "Optional content handling metadata.",
        ),
        (
            "Content-Range",
            "Communicates partial content ranges.",
            "optional",
            "Informational",
            "Optional partial-content metadata.",
        ),
        (
            "Allow",
            "Lists allowed methods for the target resource.",
            "optional",
            "Informational",
            "Optional method metadata.",
        ),
        (
            "Accept-Patch",
            "Indicates supported patch document formats.",
            "optional",
            "Informational",
            "Optional method capability metadata.",
        ),
        (
            "Accept-Post",
            "Indicates supported post formats.",
            "optional",
            "Informational",
            "Optional method capability metadata.",
        ),
    ):
        register(
            canonical_name,
            "content_metadata",
            purpose,
            expected=expected,
            risk_if_missing=risk_if_missing,
            recommendation_missing=(
                "Consider explicitly declaring the response media type with Content-Type."
                if canonical_name == "Content-Type"
                else None
            ),
            notes=notes,
        )

    register(
        "Set-Cookie",
        "cookies_sessions",
        "Sets cookie values and related browser attributes.",
        expected="contextual",
        notes="Contextual because not all public pages need cookies.",
    )

    for canonical_name, purpose, expected, notes in (
        (
            "Location",
            "Communicates a redirect or alternate resource location.",
            "contextual",
            "Contextual redirect metadata.",
        ),
        (
            "Refresh",
            "Communicates a client-side refresh or redirect instruction.",
            "optional",
            "Optional client-side redirect metadata.",
        ),
        (
            "Link",
            "Communicates related resource or navigation link metadata.",
            "optional",
            "Classified under Redirect & Location for stable primary categorization.",
        ),
    ):
        register(
            canonical_name,
            "redirect_location",
            purpose,
            expected=expected,
            notes=notes,
        )

    for canonical_name, purpose, expected, notes in (
        (
            "Access-Control-Allow-Origin",
            "Communicates allowed cross-origin origins.",
            "contextual",
            "CORS behavior is contextual.",
        ),
        (
            "Access-Control-Allow-Credentials",
            "Communicates whether credentialed cross-origin requests are permitted.",
            "contextual",
            "CORS behavior is contextual.",
        ),
        (
            "Access-Control-Allow-Methods",
            "Communicates allowed cross-origin methods.",
            "contextual",
            "CORS behavior is contextual.",
        ),
        (
            "Access-Control-Allow-Headers",
            "Communicates allowed cross-origin request headers.",
            "contextual",
            "CORS behavior is contextual.",
        ),
        (
            "Access-Control-Expose-Headers",
            "Communicates headers available to browser scripts.",
            "contextual",
            "CORS behavior is contextual.",
        ),
        (
            "Access-Control-Max-Age",
            "Communicates CORS preflight cache duration.",
            "contextual",
            "CORS behavior is contextual.",
        ),
        (
            "Origin-Agent-Cluster",
            "Communicates origin-keyed agent clustering behavior.",
            "contextual",
            "Cross-origin browser behavior is contextual.",
        ),
    ):
        register(
            canonical_name,
            "cors_cross_origin_access",
            purpose,
            expected=expected,
            notes=notes,
        )

    for canonical_name, purpose, notes in (
        ("CF-Ray", "Indicates Cloudflare edge request handling.", "Infrastructure indicator."),
        ("CF-Cache-Status", "Indicates Cloudflare cache handling.", "Infrastructure indicator."),
        ("X-Cache", "Communicates cache behavior from a proxy or edge layer.", "Infrastructure indicator."),
        ("X-Served-By", "Communicates the serving edge or cache node.", "Infrastructure indicator."),
        ("Via", "Indicates that a proxy or intermediary handled the request.", "Infrastructure indicator."),
        ("X-Backend-Server", "Communicates backend server identification.", "Infrastructure indicator."),
        ("Fastly-Debug-Digest", "Communicates Fastly debugging data.", "Infrastructure indicator."),
        ("X-Fastly-Request-ID", "Communicates Fastly request tracing data.", "Infrastructure indicator."),
        ("X-Akamai-Transformed", "Communicates Akamai transformation behavior.", "Infrastructure indicator."),
        ("X-CDN", "Communicates CDN platform identification.", "Infrastructure indicator."),
        ("X-Proxy-Cache", "Communicates proxy cache behavior.", "Infrastructure indicator."),
        ("X-Cache-Hits", "Communicates proxy or edge cache hit counts.", "Infrastructure indicator."),
        ("X-Timer", "Communicates timing data from intermediary infrastructure.", "Infrastructure indicator."),
        ("Fly-Request-Id", "Communicates Fly.io request tracing data.", "Infrastructure indicator."),
        ("Render-Origin-Server", "Communicates Render origin infrastructure details.", "Infrastructure indicator."),
        ("Vercel-Cache", "Communicates Vercel cache behavior.", "Infrastructure indicator."),
        ("X-Vercel-Id", "Communicates Vercel request tracing data.", "Infrastructure indicator."),
        ("X-Netlify-Cache", "Communicates Netlify cache behavior.", "Infrastructure indicator."),
        ("X-Platform", "Communicates platform or hosting identification.", "Infrastructure indicator."),
    ):
        register(
            canonical_name,
            "cdn_proxy_edge_infrastructure",
            purpose,
            expected="optional",
            notes=notes,
        )

    for canonical_name, purpose, notes in (
        ("Server", "Communicates server software identification.", "Informational server disclosure."),
        ("X-Powered-By", "Communicates framework or runtime identification.", "Informational framework disclosure."),
        ("X-AspNet-Version", "Communicates ASP.NET version identification.", "Informational framework disclosure."),
        ("X-Generator", "Communicates site generator or framework identification.", "Informational application disclosure."),
        ("X-Runtime", "Communicates application runtime timing or identifiers.", "Informational application disclosure."),
        ("X-Request-ID", "Communicates request tracing identifiers.", "Informational tracing disclosure."),
        ("X-Correlation-ID", "Communicates correlation identifiers for tracing.", "Informational tracing disclosure."),
        ("X-Amzn-Trace-Id", "Communicates AWS request tracing identifiers.", "Informational tracing disclosure."),
    ):
        register(
            canonical_name,
            "server_application_disclosure",
            purpose,
            expected="optional",
            notes=notes,
        )

    for canonical_name, purpose, expected, notes in (
        ("Connection", "Communicates connection handling preferences.", "optional", "Protocol metadata."),
        ("Keep-Alive", "Communicates keep-alive behavior.", "optional", "Protocol metadata."),
        ("Alt-Svc", "Communicates alternative service availability.", "contextual", "Contextual protocol metadata."),
        ("Upgrade", "Communicates protocol upgrade behavior.", "optional", "Protocol metadata."),
        ("Date", "Communicates the origin or intermediary response date.", "optional", "Protocol metadata."),
        ("Early-Data", "Communicates early data handling.", "optional", "Protocol metadata."),
        ("Retry-After", "Communicates retry timing guidance.", "optional", "Protocol metadata."),
        (
            "Upgrade-Insecure-Requests",
            "Communicates insecure request upgrade preferences.",
            "optional",
            "Protocol or browser preference metadata.",
        ),
    ):
        register(
            canonical_name,
            "protocol_connection_behaviour",
            purpose,
            expected=expected,
            notes=notes,
        )

    for canonical_name, purpose, expected, notes in (
        ("Report-To", "Communicates browser reporting destinations.", "contextual", "Contextual reporting metadata."),
        ("Reporting-Endpoints", "Communicates reporting endpoint definitions.", "contextual", "Contextual reporting metadata."),
        ("NEL", "Communicates network error logging behavior.", "contextual", "Contextual monitoring metadata."),
        ("Server-Timing", "Communicates server-side timing metrics.", "optional", "Informational timing metadata."),
        (
            "Timing-Allow-Origin",
            "Communicates which origins may access timing information.",
            "optional",
            "Informational timing metadata.",
        ),
    ):
        register(
            canonical_name,
            "reporting_monitoring",
            purpose,
            expected=expected,
            notes=notes,
        )

    for canonical_name, purpose in (
        ("X-XSS-Protection", "Legacy browser XSS filtering control."),
        ("Public-Key-Pins", "Deprecated HTTP public key pinning control."),
        ("Public-Key-Pins-Report-Only", "Deprecated report-only public key pinning control."),
        ("Expect-CT", "Legacy certificate transparency expectation control."),
        ("Feature-Policy", "Legacy browser feature access policy."),
        ("Pragma", "Legacy cache-related control header."),
    ):
        register(
            canonical_name,
            "legacy_deprecated",
            purpose,
            expected="deprecated",
            deprecated=True,
            legacy=True,
            interpretation_present=(
                f"The response includes the legacy or deprecated {canonical_name} header."
            ),
            notes="Legacy or deprecated header preserved for visibility.",
        )

    return knowledge_base


HEADER_KNOWLEDGE_BASE = _build_header_knowledge_base()
