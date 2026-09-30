# Site Inspector Technical Design Specification (TDS)

**Volume I — Project Constitution**

**Document Version:** 1.0
**Project Version Covered:** Current v1.1 → Target v1.2
**Status:** Authoritative Engineering Specification

---

# 1. Purpose of this Document

This document is the authoritative engineering specification for the Site Inspector project.

It defines the project's philosophy, scope, architecture, implementation standards, reporting standards, and long-term direction.

The source code is an implementation of this specification.

If implementation and this specification disagree, **this specification takes precedence** unless it has been explicitly revised.

This document exists so that any competent software engineer can implement, maintain, or extend Site Inspector without relying on tribal knowledge or historical implementation details.

---

# 2. Project Identity

Site Inspector is a passive website operational audit system.

It is designed to collect publicly observable configuration evidence from a website and transform that evidence into structured operational knowledge.

Site Inspector is **not** a penetration testing tool.

It is **not** a vulnerability scanner.

It is **not** an exploitation framework.

It is **not** a crawler.

It is **not** an offensive security tool.

Its primary purpose is to provide website owners, developers, consultants, hosting providers, and system administrators with a comprehensive understanding of a website's publicly exposed operational configuration.

The project focuses on observation, interpretation, and explanation rather than exploitation.

---

# 3. Mission Statement

The mission of Site Inspector is to transform publicly observable HTTP and TLS configuration into clear, structured, evidence-based operational intelligence.

The software should help users understand:

* how their website behaves,
* how it is configured,
* what infrastructure characteristics are observable,
* what operational improvements may be beneficial,
* and which configuration decisions deserve further investigation.

The software must never exaggerate findings or imply compromise where none has been demonstrated.

---

# 4. Core Philosophy

Every implementation decision within Site Inspector shall follow five guiding principles.

## 4.1 Passive First

Site Inspector shall never perform intrusive behaviour.

Evidence shall be collected only through standard web interactions that are equivalent to a normal visitor requesting the homepage of a website.

The software exists to observe publicly available configuration rather than actively interrogate systems.

---

## 4.2 Evidence Before Interpretation

Evidence is the foundation of the system.

Every recommendation, observation, finding, and risk assessment must originate from collected evidence.

The software shall never invent findings that cannot be supported by observable data.

---

## 4.3 Explanation Before Judgement

The software should explain what was observed before assigning operational significance.

Users should understand **why** a recommendation exists rather than simply being told that something is "good" or "bad."

---

## 4.4 Conservative Risk Assessment

Risk classifications represent operational impact rather than theoretical security concerns.

High risk shall be reserved for objectively significant operational issues.

Minor configuration improvements should never be described using alarmist language.

---

## 4.5 Complete Visibility

The software should expose as much useful information as practical from the collected evidence.

Site Inspector shall never intentionally hide response headers or other observable information simply because they are not currently interpreted.

Unknown information is still valuable information.

---

# 5. Design Principles

The following principles are mandatory throughout the project.

* Collect everything that is reasonably observable.
* Preserve raw evidence.
* Categorise evidence.
* Interpret evidence.
* Generate findings.
* Produce recommendations.
* Calculate operational risk.
* Present information hierarchically.

This order shall never be reversed.

Risk is a summary of evidence, not the starting point.

---

# 6. Operational Workflow

Every scan shall follow the same deterministic workflow.

```
Collect Evidence
        │
        ▼
Normalise Evidence
        │
        ▼
Categorise Evidence
        │
        ▼
Generate Observations
        │
        ▼
Generate Interpretations
        │
        ▼
Generate Recommendations
        │
        ▼
Calculate Operational Risk
        │
        ▼
Produce Report
```

Each stage is independent and should remain independently testable.

---

# 7. Deterministic Behaviour

Site Inspector shall be deterministic.

Given the same website response, the software shall always produce identical:

* evidence,
* observations,
* findings,
* recommendations,
* operational risk,
* and report output.

The project shall not rely on probabilistic reasoning or AI-generated interpretation.

All interpretation rules shall be explicitly documented and version controlled.

---

# 8. Scope

Site Inspector analyses configuration that is publicly observable from a standard page request.

Examples include, but are not limited to:

* HTTP response behaviour
* Redirect behaviour
* Response headers
* TLS certificate information
* Cookie configuration
* Compression
* Cache configuration
* Infrastructure indicators
* CMS fingerprints
* HTML metadata
* Protocol information
* Payload characteristics

Future versions may extend this list without changing the passive philosophy.

---

# 9. Non-Goals

The following activities are explicitly outside the scope of Site Inspector.

* Port scanning
* Directory enumeration
* Login testing
* Credential testing
* Vulnerability exploitation
* SQL injection testing
* XSS payload testing
* Automated crawling
* Brute force attacks
* Endpoint discovery
* Malware detection
* Source code auditing
* Active penetration testing

Support for these activities shall not be introduced into Version 1.x.

---

# 10. Evidence Hierarchy

Every piece of information collected by Site Inspector belongs to one of four layers.

## Layer 1 — Evidence

Objective facts collected directly from the website.

Example:

```
Strict-Transport-Security:
Missing
```

---

## Layer 2 — Observation

A factual statement derived from evidence.

Example:

```
The response does not include an HSTS header.
```

---

## Layer 3 — Interpretation

Operational explanation.

Example:

```
Browsers are not instructed to enforce HTTPS for future requests.
```

---

## Layer 4 — Recommendation

Professional guidance.

Example:

```
If HTTPS is intended to be permanently enforced, consider enabling HSTS after confirming that all resources are served securely.
```

---

## Layer 5 — Risk

Operational summary.

Example:

```
Medium
```

Risk shall never replace evidence.

Evidence shall always remain visible to the user.

---

# 11. Reporting Philosophy

Reports should resemble a consultant's operational assessment rather than an automated vulnerability scanner.

The report should answer three questions:

1. What was observed?
2. Why does it matter?
3. What should the user consider doing next?

It should avoid unnecessary alarmism and avoid presenting speculative conclusions as facts.

---

# 12. Version Roadmap

## Current Implementation

Version 1.1

The current implementation provides the baseline passive audit functionality and serves as the foundation for future development.

## Target Implementation

Version 1.2

Version 1.2 expands Site Inspector into a comprehensive configuration intelligence engine while preserving the passive single-request philosophy.

All new work described in subsequent volumes applies to Version 1.2 unless otherwise stated.

---

# 13. Long-Term Vision

Site Inspector is intended to evolve into a professional operational auditing platform capable of producing consultant-grade reports from passive configuration analysis.

Future growth should prioritise greater breadth of observable evidence, richer interpretation, improved reporting, and modular extensibility without compromising the project's passive operating model.

The software should become a trusted reference tool for understanding website configuration rather than a tool for testing or exploiting websites.
