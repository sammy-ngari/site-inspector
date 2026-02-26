from utils import fetch_site
import time
import ssl
import socket
from datetime import datetime

def basic_check(domain):
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

def ssl_check(domain):
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