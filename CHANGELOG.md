# Changelog

This changelog is written for contributors, not only for end users.

If you are new to this repository, read this file as a high-level explanation of what
Version `v1.2` introduced, why the codebase is shaped the way it is, and where future
changes should generally be made.

## v1.2

### Release Summary

Version `v1.2` turns Site Inspector from a smaller direct-output scanner into a more
structured passive analysis tool.

The core idea of the project did not change:

- The tool remains passive.
- The tool still relies on one standard HTTP GET request to the target.
- The tool does not crawl, brute-force, exploit, or probe beyond the observed response.

What did change is the internal architecture and the quality of the output:

- Scan data is now collected into one canonical structured object.
- Interpretation is now separated from raw collection.
- Risk evaluation is now based on structured findings instead of ad hoc checks.
- The CLI can now emit either a human-readable terminal report or structured JSON.
- The terminal report is now much more readable and organized.

### Why This Release Matters

Before `v1.2`, the project worked more like a chain of independent helper functions that
returned partial dictionaries and were printed directly.

That older approach was fine for a smaller tool, but it became limiting once we needed:

- richer header analysis
- explicit evidence and findings
- deterministic reporting
- future-friendly JSON output
- cleaner separation between collection, interpretation, and presentation

`v1.2` addresses that by treating the scan as a pipeline:

1. Collect raw facts from the target.
2. Normalize those facts into one shared scan result shape.
3. Interpret the facts through conservative rules.
4. Score the interpreted findings.
5. Render the result for humans or machines.

### Contributor Mental Model

If you are adding new behavior, use this rule of thumb:

- Put raw data collection in `scanner.py`.
- Put reusable network/input helpers in `utils.py`.
- Put deterministic reference data in `knowledge_base/`.
- Put interpretation rules in `rules/`.
- Put overall scoring and risk wording in `risk.py`.
- Put terminal presentation in `report.py`.
- Put CLI entry behavior in `main.py`.

This separation is intentional and is one of the biggest design improvements in `v1.2`.

### Major Architectural Changes

#### 1. Canonical `ScanResult` model introduced

The largest change in `v1.2` is the move to a unified scan result object produced by
`collect_scan_result()` in `scanner.py`.

Instead of passing many unrelated dictionaries through the program, the tool now builds
one structured object containing:

- project metadata
- target metadata
- request metadata
- connectivity results
- TLS results
- HTTP response metadata
- header analysis output
- cookie analysis output
- cache analysis output
- compression analysis output
- infrastructure indicators
- platform detection output
- HTML metadata
- performance indicators
- evidence
- observations
- findings
- recommendations
- risk summary
- recoverable errors

Why this matters:

- every layer now works from the same shared structure
- terminal output and JSON output now describe the same scan
- future contributors can add fields without redesigning the whole pipeline
- rule evaluation can now trace findings back to evidence consistently

#### 2. Collection and interpretation are now separate stages

In `v1.2`, the scanner does not try to do everything.

The intended flow is now:

- `scanner.py` collects facts
- `rules/` interprets facts
- `risk.py` scores findings
- `report.py` displays the result

This is an important contributor-facing change because new logic should usually not be
added directly into the report layer or into the CLI.

#### 3. Deterministic rule-driven output introduced

The `rules/` package was added so that findings are generated in a structured, traceable,
and repeatable way.

The rule engine currently builds:

- evidence objects
- observations
- findings
- recommendations

The package also sorts and deduplicates these objects so that output remains stable
between runs.

This is important for:

- readable reports
- consistent JSON output
- future testing
- contributor confidence when changing the logic

### File-By-File Breakdown

#### `main.py`

`main.py` was refactored from a simpler procedural CLI into a proper entry point for the
full `v1.2` pipeline.

Changes introduced:

- version updated from `v1.1` to `v1.2`
- inspection now runs through `collect_scan_result()` plus `analyze_risk()`
- `--json` output was added
- `--version` behavior was preserved
- interactive domain entry was preserved
- machine-readable fallback output was added for JSON-mode failures

Why it matters:

- contributors now have one obvious CLI flow to extend
- human output and JSON output are built from the same scan object
- failure handling is clearer and more predictable

#### `utils.py`

`utils.py` became the shared home for request normalization and low-level network helpers.

Changes introduced:

- added `REQUEST_TIMEOUT_SECONDS`
- added `normalize_url()`
- added `extract_hostname()`
- added redirect-history serialization
- changed `fetch_site()` to always return a structured result
- added structured request error reporting instead of returning `None`

Why it matters:

- callers no longer have to guess whether a request succeeded
- URL handling is consistent across the project
- redirect data is now available to later analysis and reporting stages

#### `scanner.py`

`scanner.py` saw the largest structural expansion in this release.

It still owns raw and lightweight derived collection, but it now produces a much richer
model.

Major additions include:

- stronger connectivity collection with final URL, redirect chain, timing, size, and errors
- structured TLS inspection with certificate metadata
- header normalization and categorized header output
- cookie parsing with per-cookie details and summary counts
- cache analysis with parsed directives
- compression analysis
- infrastructure indicator extraction
- platform detection with evidence and confidence
- lightweight HTML metadata extraction
- performance classification
- final `collect_scan_result()` assembly

Important design note:

`scanner.py` is intentionally still a large file in `v1.2`.
That is acceptable for this release, but the internal helpers added here are designed to
make future modular extraction easier.

#### `knowledge_base/headers.py`

This file was added as a deterministic header reference library.

It now defines:

- stable header categories
- metadata for known headers
- expected presence rules
- recommended values where relevant
- interpretation text for present and missing states
- recommendation text
- conservative risk labels and scores

Why it matters:

- header handling is no longer just a hardcoded presence check
- contributors can extend header intelligence without rewriting scanner logic
- report output and findings now share a single source of header truth

#### `rules/`

The `rules/` package is one of the most important additions in `v1.2`.

It separates interpretation from collection and provides a stable place to add new
findings.

Current layout:

- `rules/__init__.py`
  Combines evaluator outputs, deduplicates by ID, and sorts the final result.
- `rules/common.py`
  Defines shared object builders and deterministic sorting helpers.
- `rules/core.py`
  Handles connectivity, TLS, cache, compression, and platform findings.
- `rules/headers.py`
  Translates known and unknown header states into evidence and findings.
- `rules/cookies.py`
  Generates cookie-related evidence and findings from structured cookie data.

Why it matters:

- new findings should usually be added here rather than in `risk.py` or `report.py`
- findings are now traceable to evidence IDs
- contributor changes can stay scoped to a single rule domain

#### `risk.py`

`risk.py` was refactored to consume structured findings instead of running its own
disconnected checks.

Changes introduced:

- calls `build_interpretation_result()` from `rules/`
- populates `evidence`, `observations`, `findings`, and `recommendations` on the scan
- computes total risk score from finding scores
- applies conservative thresholds for `Low`, `Medium`, and `High`
- supports explicit high-risk overrides for severe states
- generates consultant-style summary wording

Why it matters:

- the risk layer is now clearly downstream of interpretation
- adding a new finding usually does not require rewriting the risk engine
- summary language is more operational and less purely technical

#### `report.py`

The report layer was fully rewritten around the `ScanResult` structure.

Instead of printing a short flat summary, the terminal report now has explicit sections
for:

- executive summary
- target and request context
- connectivity
- transport security
- HTTP response metadata
- header overview
- categorized headers
- cookies and sessions
- cache and freshness
- compression and transfer
- infrastructure indicators
- platform detection
- HTML metadata
- performance indicators
- operational findings
- recommendations
- raw evidence summary

The report also now includes a much stronger visual hierarchy:

- centered headings
- section spacing
- separators
- color-coded risk and status labels when supported
- safe fallback to plain output when styling is unavailable
- wrapped text for narrower terminals

Why it matters:

- the terminal output is usable as a real consultant-style summary
- contributors can add new sections without changing the rest of the pipeline
- human-readable output remains aligned with JSON-mode data

#### `README.md`

The README was updated to reflect the `v1.2` project state.

Changes introduced:

- corrected project version to `v1.2`
- documented direct domain usage
- documented `--json`
- documented `--version`
- linked to this changelog

Why it matters:

- the repository documentation now matches the implemented tool
- new contributors have correct usage examples

### New Analysis Capabilities Added

`v1.2` adds or expands the following contributor-visible capabilities:

- full target normalization and final URL tracking
- redirect chain preservation
- richer TLS certificate metadata
- deterministic raw-header preservation
- header categorization by domain
- expected-missing header reporting
- deprecated-header tracking
- vendor-specific or unknown header retention
- per-cookie attribute analysis
- cache directive parsing
- compression-method detection
- infrastructure hints from response headers
- lightweight CMS/platform evidence
- lightweight HTML metadata extraction
- page weight classification
- structured risk evidence, findings, and recommendations

### Output Model Changes

Two output modes are now first-class:

#### Human-readable terminal output

This is the default contributor-facing and operator-facing mode.
It is intended to be readable by non-developers and useful during manual review.

#### JSON output

The `--json` flag now exposes the full structured scan result.

This matters for contributors because it creates a stable interface for:

- downstream tooling
- automation
- future tests
- future integrations

JSON mode also includes structured fallback results when inspection fails, so callers
receive machine-readable failure data instead of unstructured CLI text.

### Error Handling Improvements

This release improves resilience without adding aggressive retry or probing behavior.

Important changes:

- request failures are captured as structured connectivity errors
- TLS failures are returned as structured TLS results
- unreachable targets still produce a valid scan object
- JSON mode can still emit a valid result on failure
- recoverable cookie parsing issues can be preserved instead of crashing the run

This makes the tool safer to extend and easier to test.

### Design Constraints Preserved In `v1.2`

Contributors should keep these constraints in mind when building on this release:

- the tool should remain passive
- the tool should remain based on one primary standard page request
- the tool should avoid crawling and exploit-oriented behavior
- the tool should remain conservative in its conclusions
- findings should stay traceable to observed evidence
- unknown headers should be preserved rather than discarded
- reporting should distinguish between observed facts and interpretation

These constraints are not accidental; they are central to the design of this project.

### How To Extend The System After `v1.2`

If you want to add a new capability, the usual path is:

1. Add raw collection or extraction in `scanner.py` if the data is not already present.
2. Add reference data in `knowledge_base/` if the feature depends on stable metadata.
3. Add interpretation logic in `rules/`.
4. Let `risk.py` consume the new findings naturally through scoring unless a special
   override is truly necessary.
5. Update `report.py` only for presentation needs.
6. Update `README.md` or this changelog when the contributor-facing behavior changes.

Examples:

- Add a new header:
  update `knowledge_base/headers.py`, ensure `scanner.py` includes it in normalized
  analysis, and add rule handling only if a specific finding should be generated.
- Add a new infrastructure indicator:
  collect the raw signal in `scanner.py`, store it in the infrastructure section, then
  decide whether it should remain informational or produce findings through `rules/`.
- Add a new report section:
  prefer deriving it from existing `ScanResult` data rather than doing fresh collection
  inside `report.py`.

### Non-Goals Of This Release

To help new contributors understand the current boundary, `v1.2` does not attempt to be:

- a penetration testing framework
- a crawler
- a multi-page scanner
- a deep browser automation tool
- a full HTML or JavaScript analyzer
- a comprehensive CSP parser
- a broad plugin ecosystem yet

The release is intentionally conservative and focused on reliable passive inspection.

### Practical Impact For Future Contributors

After `v1.2`, contributors should notice that the project is easier to reason about:

- there is a clearer data flow
- the code is more modular in responsibility even where files are still large
- output is easier to test because it is structured
- the report is easier to extend because it consumes a stable scan object
- findings are easier to explain because they are linked to evidence

In short, `v1.2` is not only a feature release.
It is also the release that establishes the structure future work should build on.
