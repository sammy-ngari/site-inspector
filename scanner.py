"""
Data collection layer.

Extracts measurable attributes from HTTP responses,
TLS metadata, and HTML content.
"""

from utils import fetch_site
import time
import ssl
import socket
from datetime import datetime

def basic_check(domain):

    """
    Perform baseline connectivity and response analysis.

    Measures:
        - Reachability
        - Final URL
        - HTTP status code
        - Response time
        - Redirect count
        - Headers
        - Body content
        - Payload size

    Returns
    -------
    dict
        Structured response data for downstream processing.
    """

    start = time.time()
    data = fetch_site(domain)
    end = time.time()

    if not data:
        return {"reachable": False}
    
    return {
        "reachable": True,
        "final_url": data["url"],
        "status_code": data["status_code"],
        "response_time": round(end - start, 2),
        "redirects": len(data["history"]),
        "headers": data["headers"],
        "content": data["content"],
        "size": data["size"]
    }

def security_headers(headers):

    """
    Check presence of selected security-related HTTP headers.

    Parameters
    ----------
    headers : Mapping
        Response headers from the HTTP request.

    Returns
    -------
    dict
        Mapping of header name → "Present" | "Missing".
    """

    important_headers = {
        "Strict-Transport-Security": "HSTS",
        "Content-Security-Policy": "CSP",
        "X-Content-Type-Options": "X-Content-Type-Options",
        "X-Frame-Options": "X-Frame-Options",
        "Referrer-Policy": "Referrer-Policy"
    }

    results = {}

    for header, name in important_headers.items():
        results[name] = "Present" if header in headers else "Missing"

    return results

def compression_check(headers):
    
    """
    Determines whether HTTP compression is enabled.
    Derived from Content-Encoding header.
    """

    encoding = headers.get("Content-Encoding", "").lower()

    if "gzip" in encoding or "br" in encoding:
        return {"enabled": True, "method": encoding}
    
    return {"enabled": False, "method": "None"}

def cache_analysis(headers):

    """
    Evaluates browser caching configuration from response headers.
    """

    cache_control = headers.get("Cache-Control")
    expires = headers.get("Expires")

    return{
        "Cache-Control": cache_control,
        "Expires": expires,
        "configured": bool(cache_control or expires)
    }

def cookie_security(headers):

    """
    Inspects Set-Cookie headers for Secure, HttpOnly, and SameSite flags.
    """

    cookies = headers.get("Set-Cookie")

    if not cookies:
        return {"present": False}
    
    cookies = cookies.lower()

    return {
        "present": True,
        "secure_flag": "secure" in cookies,
        "httponly_flag": "httponly" in cookies,
        "samesite_flag": "samesite" in cookies
    }

def server_fingerprint(headers):

    """
    Extracts infrastructure hints from response headers.
    """

    return {
        "Server": headers.get("Server"),
        "X-Powered-By": headers.get("X-Powered-By"),
        "via": headers.get("Via"),
        "cf-ray": headers.get("CF-Ray")  # Cloudflare specific
    }

def ssl_check(domain):

    """
    Retrieve TLS certificate metadata and calculate remaining validity.

    Parameters
    ----------
    domain : str
        Hostname without scheme.

    Returns
    -------
    dict
        {
            "Valid": bool,
            "Days Left": int  # only if valid
        }
    """

    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                expiry = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
                days_left = (expiry - datetime.utcnow()).days

                return{
                    "Valid": True,
                    "Days Left": days_left,
                }
            
    except:
        return {"Valid": False}
    
def detect_cms(content):

    """
    Perform heuristic CMS detection based on HTML markers.

    Parameters
    ----------
    content : str
        HTML response body.

    Returns
    -------
    str
        Identified platform name or "Unknown".
    """
    
    content = content.lower()

    if "wp-content" in content or "wp-json" in content:
        return "WordPress"
        
    if "cdn.shopify.com" in content:
        return "Shopify"
        
    if "wixstatic.com" in content:
        return "Wix"
        
    if "/sites/default/" in content:
        return "Drupal"
        
    if "/components/com_" in content:
        return "Joomla"
        
    return "Unknown"