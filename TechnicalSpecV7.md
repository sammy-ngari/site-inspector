# Site Inspector Technical Design Specification (TDS)

**Volume VII — Implementation Standards, Code Quality & Documentation Rules**

**Document Version:** 1.0
**Project Version Covered:** Current v1.1 → Target v1.2
**Status:** Authoritative Engineering Specification
**Depends On:** Volume I — Project Constitution
**Depends On:** Volume II — System Architecture & Implementation Model
**Depends On:** Volume III — Data Models & Schemas
**Depends On:** Volume IV — Header Knowledge Base
**Depends On:** Volume V — Rule Engine, Findings & Risk Interpretation
**Depends On:** Volume VI — Reporting, CLI Output & JSON Output

---

# 1. Purpose of this Volume

This volume defines how Site Inspector code must be written, documented, refactored, reviewed, and maintained.

The purpose is to ensure that the codebase remains readable, modular, deterministic, and aligned with the project identity.

Site Inspector is intended to be a professional backend-focused operational audit tool. Its implementation should reflect that.

The code should be understandable by a backend developer, maintainable by a future contributor, and clear enough for Codex to extend without repeatedly breaking architectural boundaries.

---

# 2. Primary Implementation Rule

Codex must work incrementally.

The existing v1.1 codebase is the baseline.

Version 1.2 must improve it without unnecessary rewrites.

Codex must not replace the entire project with a new architecture in one step unless explicitly instructed.

Preferred implementation style:

```text id="ij218p"
small changes
clear diffs
preserved behaviour
added structure
improved correctness
stable CLI
```

Avoid:

```text id="9rc69t"
large rewrites
renaming everything at once
merging modules
adding dependencies casually
changing CLI behaviour without reason
```

---

# 3. Python Version

Site Inspector must support:

```text id="o79jkn"
Python 3.10+
```

Use standard Python features available in Python 3.10.

Do not require newer syntax if not necessary.

---

# 4. Dependency Rules

Dependencies must remain minimal.

Current accepted dependency family:

```text id="2ih86g"
requests
certifi
charset-normalizer
idna
urllib3
```

Preferred standard library modules:

```text id="ezpywe"
argparse
datetime
email.utils
html.parser
json
re
socket
ssl
time
typing
urllib.parse
```

Do not add these unless explicitly approved:

```text id="dv2vvm"
BeautifulSoup
Selenium
Scrapy
httpx
nmap
security scanning libraries
web frameworks
async frameworks
database libraries
ORMs
```

A dependency may be proposed only if:

```text id="obqayq"
it solves a real problem,
it does not change the passive model,
it is lightweight,
it does not introduce aggressive scanning behaviour,
and the reason is documented.
```

---

# 5. Module Boundary Rules

Site Inspector must preserve clean separation of responsibility.

## 5.1 `main.py`

Allowed:

```text id="gztt1q"
CLI parsing
version handling
interactive prompt
top-level orchestration
exit codes
banner control
```

Not allowed:

```text id="qlcs2k"
HTTP fetching logic
header interpretation logic
risk scoring logic
report formatting beyond banner
HTML parsing
cookie parsing
```

## 5.2 `utils.py`

Allowed:

```text id="y4ebhn"
URL normalization
hostname extraction
HTTP request execution
low-level request error normalization
generic helper functions
```

Not allowed:

```text id="93l9zv"
risk scoring
report printing
CMS interpretation
header recommendations
finding generation
```

## 5.3 `scanner.py`

Allowed:

```text id="twnj27"
evidence collection
response timing
TLS evidence
header evidence
cookie evidence
HTML metadata evidence
CMS evidence
performance evidence from already collected data
```

Not allowed:

```text id="m96r5q"
console output
risk scoring
recommendation wording
additional endpoint requests
```

## 5.4 `risk.py`

Allowed:

```text id="44r7ar"
risk aggregation
risk thresholds
risk overrides
summary generation from findings
```

Not allowed:

```text id="i3t1xl"
network requests
HTML parsing
CLI prompts
console formatting
```

## 5.5 `report.py`

Allowed:

```text id="i9cj0e"
console formatting
section rendering
JSON output formatting if not split into another file
value display conversion
finding sorting for display
```

Not allowed:

```text id="np1u40"
evidence collection
risk scoring
HTTP requests
CMS detection
cookie parsing
```

## 5.6 `knowledge_base/`

Allowed:

```text id="bhd5lc"
header definitions
known header categories
interpretation templates
recommended values
deprecated header metadata
```

Not allowed:

```text id="9d0jwq"
network calls
printing
runtime scanning
```

## 5.7 `rules/`

Allowed:

```text id="3bvtfl"
evaluate evidence
generate observations
generate findings
generate recommendations
apply deterministic rules
```

Not allowed:

```text id="ksoi3k"
fetch websites
print reports
parse CLI arguments
perform extra probes
```

---

# 6. Naming Conventions

Use clear, descriptive names.

Function names should describe action:

```python id="s1l03d"
normalize_url()
extract_hostname()
fetch_site()
collect_tls_evidence()
categorize_headers()
evaluate_header_rules()
calculate_risk_summary()
print_executive_summary()
```

Avoid vague names:

```python id="l1fv3d"
do_scan()
check()
process()
handle()
thing()
data_stuff()
```

Variable names should describe contents:

Good:

```python id="4qpx1c"
response_headers
normalized_headers
categorized_headers
scan_result
tls_result
cookie_summary
```

Bad:

```python id="83gble"
x
stuff
res
out
final
```

---

# 7. Function Design Rules

Functions should be small and single-purpose.

A function should generally do one of these:

```text id="stg17d"
collect one type of evidence
normalize one structure
evaluate one group of rules
render one report section
```

A function should not:

```text id="qnv7ah"
fetch a site,
parse HTML,
score risk,
and print output
```

If a function requires more than one paragraph to explain what it does, it is probably too broad.

---

# 8. Type Hints

Use type hints where they improve clarity.

Recommended:

```python id="uq2sgs"
def normalize_url(value: str) -> str:
    ...

def fetch_site(url: str) -> dict:
    ...

def evaluate_header_rules(scan_result: dict) -> list[dict]:
    ...
```

Do not overcomplicate v1.2 with custom classes unless explicitly approved.

Typed dictionaries or dataclasses may be considered in a later version, but v1.2 may remain dictionary-based for simplicity and continuity.

---

# 9. Dictionary Access Rules

Use defensive dictionary access when dealing with collected evidence.

Preferred:

```python id="na2pyp"
headers.get("Content-Type")
```

Avoid:

```python id="es5c2p"
headers["Content-Type"]
```

unless the key is guaranteed by schema construction.

When creating schema-compatible objects, include required keys even when values are unavailable.

Example:

```python id="xjhd2v"
{
    "valid": False,
    "days_until_expiry": None,
    "error": "TLS certificate could not be verified"
}
```

---

# 10. Error Handling Rules

Normal operational failures must not crash the program.

Expected failures include:

```text id="b5jk6e"
DNS failure
timeout
TLS verification failure
missing headers
empty response body
non-HTML response
invalid user input
redirect failure
```

These should produce structured error objects.

Bare exception handling is forbidden.

Avoid:

```python id="srrozn"
except:
    return {"Valid": False}
```

Preferred:

```python id="rkzn2t"
except (ssl.SSLError, socket.timeout, socket.gaierror, OSError, KeyError, ValueError) as exc:
    return {
        "checked": True,
        "valid": False,
        "error": "TLS certificate could not be verified",
        "exception_type": type(exc).__name__
    }
```

The console report should show friendly messages.

The JSON output should include structured errors.

---

# 11. Commenting Philosophy

Comments should explain why code exists, not repeat what the code already says.

Bad:

```python id="j7g4ms"
# Loop through headers
for header in headers:
    ...
```

Good:

```python id="80nkf5"
# Unknown headers are preserved because vendor-specific
# infrastructure hints may become classifiable in future versions.
for header in headers:
    ...
```

Bad:

```python id="goj34n"
# Set score to zero
score = 0
```

Good:

```python id="s6e0vb"
# Risk begins at zero because findings must explicitly
# contribute to the operational score.
score = 0
```

---

# 12. Docstring Standard

Every public function must include a docstring.

Docstrings must explain:

```text id="aegpm2"
purpose
parameters
return value
failure behaviour
important notes
```

Preferred format:

```python id="f8ilry"
def extract_hostname(value: str) -> str:
    """
    Extract a hostname from a user-provided domain or URL.

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

For scanner functions:

```python id="ggxq9o"
def collect_cache_evidence(headers: dict) -> dict:
    """
    Collect cache-related evidence from response headers.

    Parameters
    ----------
    headers:
        HTTP response headers from the primary request.

    Returns
    -------
    dict
        Structured cache evidence including Cache-Control,
        Expires, ETag, Last-Modified, Vary, and parsed directives.

    Notes
    -----
    This function collects evidence only. It does not decide risk.
    """
```

For rule functions:

```python id="43p0dk"
def evaluate_cookie_rules(scan_result: dict) -> list[dict]:
    """
    Generate cookie-related findings from collected cookie evidence.

    Parameters
    ----------
    scan_result:
        Complete structured scan result.

    Returns
    -------
    list[dict]
        Findings derived from cookie evidence.

    Notes
    -----
    No cookies present should not automatically generate risk.
    """
```

---

# 13. Logging and Printing Rules

Only the report layer should print scan results.

Allowed print locations:

```text id="2qmh0i"
main.py for banner or CLI-level messages
report.py for report output
```

Not allowed:

```text id="ngvogq"
scanner.py printing evidence
risk.py printing risk
rules/ printing findings
utils.py printing request errors
```

Functions should return data, not print it.

This keeps JSON output possible.

---

# 14. JSON Serialization Rules

All values in `ScanResult` must be JSON-serializable.

Avoid storing raw objects from libraries.

Do not store:

```text id="9hkpmk"
requests.Response objects
datetime objects
ssl certificate raw objects
socket objects
exception objects
```

Instead store strings, numbers, booleans, lists, dictionaries, or `None`.

Example:

Bad:

```python id="g0ignx"
"response": response
```

Good:

```python id="pre974"
"status_code": response.status_code
"headers": dict(response.headers)
"content": response.text
```

---

# 15. Deterministic Output Rules

Given the same input evidence, the same rules must produce the same findings.

Do not use:

```text id="s0x47o"
randomized wording
AI-generated conclusions
time-dependent wording unless based on collected time-sensitive evidence
non-deterministic sorting
```

Sort findings and headers consistently.

Suggested sorting:

```text id="o1gl76"
category order
then header canonical name
then severity
then finding ID
```

---

# 16. Refactoring Rules

Codex must refactor cautiously.

When refactoring:

```text id="pm68iq"
preserve existing CLI behaviour
preserve existing checks
fix known bugs first
add tests or manual test notes where possible
avoid changing too many concepts in one pass
```

Preferred v1.2 refactoring order:

```text id="rlq5em"
1. Fix bugs.
2. Normalize return structures.
3. Introduce ScanResult.
4. Add header categorization.
5. Add knowledge base.
6. Add findings.
7. Update report.
8. Add JSON output.
```

Do not start by splitting everything into many files unless explicitly requested.

The architecture allows future modularity, but implementation should remain controlled.

---

# 17. Current v1.1 Known Issues to Fix

The following issues are known in the current v1.1 codebase and should be addressed early in v1.2.

## 17.1 Implicit `None` Return in `fetch_site`

Current issue:

Request failure returns implicit `None`.

Required:

Return an explicit structured failure object.

---

## 17.2 Compression Display Bug

Current issue:

Compression report prints the literal string:

```text id="fr44lt"
Compression: Enabled ({compression['Method']})
```

Required:

Use actual dictionary key:

```python id="1jbr36"
print(f"Compression: Enabled ({compression['method']})")
```

---

## 17.3 Inconsistent Compression Key Case

Current issue:

Scanner returns:

```python id="24zpsn"
"method"
```

Report attempts:

```python id="75v0xg"
"Method"
```

Required:

Use lowercase `method` consistently.

---

## 17.4 Report Typo

Current issue:

```text id="r261nu"
OverallRisk Level
```

Required:

```text id="9tr58k"
Overall Risk Level
```

---

## 17.5 Bare Exception in TLS Check

Current issue:

TLS check catches all exceptions silently.

Required:

Catch expected exception types and return structured error details.

---

## 17.6 README Version Mismatch

Current issue:

README still references v1.0 while code uses v1.1.

Required:

Update version references consistently.

Target v1.2 documentation must reflect v1.2.

---

## 17.7 Risk Language Too Alarmist

Current issue:

Some risk wording references attacks directly.

Required:

Use operational advisory wording instead.

Example replacement:

Bad:

```text id="qi2dqq"
increased risk of XSS attacks
```

Better:

```text id="en3kq6"
Browser-side content restrictions are not explicitly configured.
```

---

## 17.8 HTTPS Redirect Interpretation Too Simplistic

Current issue:

Redirect count of zero is treated as possible missing HTTPS enforcement.

Required:

Interpret redirect behaviour more carefully.

A site can be directly accessed through HTTPS with zero redirects and still be fine.

Redirect interpretation should consider:

```text id="aj9gir"
input URL
normalized URL
final URL
scheme
redirect chain
```

Do not assume zero redirects is a problem.

---

# 18. Wording Standards in Code

The same tone rules apply to code-generated strings.

Preferred:

```text id="f9ygv9"
not observed
configuration review recommended
browser protection header not observed
server technology is publicly disclosed
```

Avoid:

```text id="d3rf4x"
dangerous
vulnerable
attack
hack
exploit
unsafe
```

Exception:

The word “attack” may appear only in educational context and should be avoided in default report output.

---

# 19. Constants and Configuration

Stable values should be defined as constants.

Examples:

```python id="0rlxde"
VERSION = "v1.2"
REQUEST_TIMEOUT_SECONDS = 10
PAGE_WEIGHT_SMALL_KB = 500
PAGE_WEIGHT_LARGE_KB = 2048
```

Avoid magic numbers inside functions.

Bad:

```python id="5gy58s"
if response_time > 2:
```

Better:

```python id="gkgv87"
SLOW_RESPONSE_THRESHOLD_SECONDS = 2.0

if response_time > SLOW_RESPONSE_THRESHOLD_SECONDS:
```

Constants should live near the module that owns them unless they become shared configuration.

---

# 20. Exit Code Rules

CLI exit codes should be simple.

Recommended:

```text id="y7ny7i"
0: successful execution
1: site unreachable or scan could not complete
2: invalid CLI usage
```

Do not create many exit codes in v1.2.

If JSON output is requested, still return appropriate exit codes while printing valid JSON.

---

# 21. Input Validation Rules

Site Inspector should accept common inputs:

```text id="okh45b"
example.com
https://example.com
http://example.com
https://example.com/path
example.com/path
```

It should normalize them safely.

It should not reject paths unnecessarily, but hostname extraction must be correct.

It should not treat user input as shell commands.

No shell execution is required.

---

# 22. Security of the Tool Itself

Site Inspector must not execute remote content.

It must not evaluate JavaScript.

It must not run shell commands based on website response data.

It must not load external scripts.

It must not follow embedded links.

It must treat all response content as untrusted text.

---

# 23. HTML Parsing Rules

For v1.2, HTML parsing should remain lightweight.

Allowed:

```text id="zc7bin"
regular expressions for simple metadata
html.parser from standard library
string search for CMS markers
```

Avoid:

```text id="h3emfr"
executing JavaScript
fetching scripts
fetching stylesheets
DOM rendering
browser automation
```

If regex is used, keep it simple and defensive.

Do not attempt to build a full browser.

---

# 24. Cookie Parsing Rules

Cookie parsing should be robust but modest.

Use standard library support where practical.

The parser should handle:

```text id="tk8hao"
Secure
HttpOnly
SameSite
Path
Domain
Expires
Max-Age
```

If cookie parsing fails, preserve the raw cookie string and add a recoverable error.

Do not crash.

---

# 25. Header Parsing Rules

Header lookup must be case-insensitive.

Raw header casing must be preserved.

Normalized lookup keys must be lowercase.

Every observed header must be retained.

Known headers must be categorized through the knowledge base.

Unknown headers must be assigned to:

```text id="5spvse"
Vendor-Specific / Unclassified
```

---

# 26. Risk Scoring Code Rules

Risk scoring must be transparent.

Avoid deeply nested logic that hides why a score changed.

Good:

```python id="fwss21"
if finding["score"] > 0:
    score += finding["score"]
    contributors.append(finding["id"])
```

Better:

```python id="xprkuq"
score = sum(finding.get("score", 0) for finding in findings)
contributors = [
    finding["id"]
    for finding in findings
    if finding.get("score", 0) > 0
]
```

Risk overrides must be explicit.

Example:

```python id="ll31ct"
if has_finding(findings, "finding.connectivity.unreachable"):
    level = "High"
    override = "Site unreachable"
```

---

# 27. Report Code Rules

Report functions should be boring and predictable.

Each report section should receive `scan_result` and print one section.

Example:

```python id="usny1k"
def print_tls_section(scan_result: dict) -> None:
    ...
```

Do not calculate TLS validity in the report.

Do not generate findings in the report.

Do not fetch missing information in the report.

---

# 28. README Documentation Rules

README must stay aligned with the code.

README should include:

```text id="r8k4zv"
project name
project purpose
passive-only scope
single primary request model
what the tool checks
what the tool does not do
requirements
installation
usage
CLI examples
version
author/maintainer
ethical use notice
```

README must include:

```text id="6599h2"
This analysis is based solely on publicly exposed configuration observed during a standard page request.
```

README must not claim penetration testing capability.

---

# 29. Changelog Rules

When v1.2 is implemented, add or update a changelog section.

Suggested format:

```text id="9ctn1w"
## v1.2

- Added structured scan result model.
- Added complete response header preservation.
- Added header categorization.
- Added header knowledge base.
- Improved TLS error handling.
- Improved report hierarchy.
- Updated risk wording to operational advisory tone.
```

If no separate `CHANGELOG.md` exists, README may contain version history.

---

# 30. Code Review Checklist

Before accepting Codex-generated changes, review:

```text id="77r7nw"
Does it preserve the single-request model?
Does it avoid crawling or probing?
Does each module respect its responsibility?
Are all observed headers preserved?
Are unknown headers categorized?
Are findings traceable to evidence?
Is risk scoring conservative?
Does CLI still work?
Does JSON output remain valid if implemented?
Does the code avoid alarmist wording?
Are errors structured?
Are docstrings clear?
```

---

# 31. Manual Test Checklist

After changes, run:

```bash id="cc2wzj"
python main.py --version
python main.py --domain example.com
python main.py
```

If JSON is implemented:

```bash id="2z65wy"
python main.py --domain example.com --json
```

Test at least:

```text id="fhejbc"
normal reachable site
site with many headers
site with minimal headers
invalid domain
HTTPS site
HTTP-only site if available
site with cookies
site without cookies
```

Do not test by scanning private or unauthorized systems.

---

# 32. Future Automated Testing Standards

Future test files may be organized as:

```text id="j89v9j"
tests/
    test_utils.py
    test_headers.py
    test_cookies.py
    test_cache.py
    test_tls.py
    test_rules.py
    test_risk.py
    test_report.py
```

Tests should use synthetic data where possible.

Avoid tests that depend on live websites unless clearly marked as integration tests.

Synthetic tests are preferred because they are deterministic.

---

# 33. Codex Instruction Block

When Codex is asked to implement Site Inspector changes, it must follow this instruction:

```text id="deu3fo"
Work incrementally from the existing v1.1 codebase.

Preserve the passive single-request model.

Do not add crawling, endpoint probing, brute-force checks, exploit checks, port scanning, or additional discovery requests.

Respect module boundaries.

Collect evidence first.

Interpret evidence second.

Report findings third.

Preserve all observed headers.

Categorize unknown headers as Vendor-Specific / Unclassified.

Use consultant-style operational language.

Keep risk scoring conservative.

Do not rewrite the entire project unless explicitly instructed.
```

---

# 34. Success Criteria for Volume VII

Implementation standards are successful if:

```text id="jkxby0"
the code remains readable,
modules remain separated,
functions remain small,
errors are handled explicitly,
docstrings explain purpose and failure behaviour,
comments explain reasoning rather than obvious code,
risk logic remains traceable,
reporting remains deterministic,
Codex can safely extend the project,
and the implementation still feels like a backend operational audit tool.
```

---

# 35. Final Implementation Rule

Site Inspector should be boring in its code and valuable in its interpretation.

The code should be simple, modular, predictable, and disciplined.

The intelligence should live in structured evidence, documented rules, and careful reporting.
