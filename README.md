# Site Inspector

**Site Inspector** is a passive website configuration auditing tool written in Python.

It analyzes a publicly accessible website and produces a human-readable health report covering availability, security configuration, and platform maintenance indicators.

This tool does **not** perform penetration testing or exploitation.
It only evaluates publicly exposed configuration and response behavior.

---

Author: Sammy Ngari  
Maintainer: Sammy Ngari

## What It Checks

* Connectivity & response behavior
* Redirect handling
* SSL certificate validity & expiry
* Security headers
* CMS detection (WordPress, Shopify, Wix, Drupal, Joomla)
* Basic operational risk interpretation
* Compression detection
* Browser caching analysis
* Cookie security inspection
* Infrastructure fingerprinting

---

## Purpose

Many website owners do not know whether their site is properly configured, secure for visitors, or maintained correctly.
This tool translates technical server responses into understandable operational insights.

---

## Requirements

Python 3.10+

Install dependencies:

pip install -r requirements.txt

---

## Usage

Run:

python main.py

Then enter a domain name (example: example.com)

---

## Important Notice

This tool performs a **passive analysis only** using standard HTTP requests.
It does not attempt to exploit vulnerabilities or access restricted areas.

It is intended for:

* self-auditing
* consent-based assessments
* educational purposes

---

## Version

v1.0 — Initial Release
