"""
Reporting layer.

Formats structured scan data and risk analysis
for console output.
"""

from risk import analyze_risk

def print_report(domain, basic, ssl_data, headers, cms, compression, cache, cookies, infra):

    """
    Render scan results to stdout.

    Parameters
    ----------
    domain : str
    basic : dict
    ssl_data : dict
    headers : dict
    cms : str
    compression : dict
    cache : dict
    cookies : dict
    infra : dict
    """

    print("\n===== WEBSITE HEALTH REPORT =====\n")

    if not basic["reachable"]:
        print("Site Unreachable.")
        return
    
    print("Domain: ", domain)
    print("Final URL: ", basic["final_url"])
    print("Status Code: ", basic["status_code"])
    print("Response Time: ", basic["response_time"], "seconds")
    print("Redirects: ", basic["redirects"])

    print("\n--- SSL ---")
    if ssl_data["Valid"]:
        print("SSL: Valid")
        print("Days until expiry: ", ssl_data["Days Left"])
    else:
        print("SSL: Invalid or Missing")

    print("\n--- Platform ---")
    print("Detected CMS: ", cms)

    print("\n--- Security Headers ---")
    for k, v in headers.items():
        print(f"{k}: {v}")

    print("\n--- Performance Configuration ---")
    if compression["enabled"]:
        print("Compression: Enabled ({compression['Method']})")
    else:
        print("Compression: Not Enabled")
    if cache["configured"]:
        print("Browser Caching: Configured")
    else:
        print("Browser Caching: Not Configured")

    print("\n--- Session Security ---")
    if not cookies["present"]:
        print("Cookies: None Detected")
    else:
        print("Secure Flag: ", "Present" if cookies["secure_flag"] else "Missing")
        print("HttpOnly Flag: ", "Present" if cookies["httponly_flag"] else "Missing")
        print("SameSite Flag: ", "Present " if cookies["samesite_flag"] else "Missing")

    print("\n--- Infrastructure Indicators ---")
    print("Server:", infra["Server"] or "Not disclosed")
    print("X-Powered-By:", infra["X-Powered-By"] or "Not disclosed")
    

    print("\n--- Risk Analysis ---")
    level, issues = analyze_risk(basic, ssl_data, headers, cms, compression, cache, cookies)
    print("OverallRisk Level:", level)
    for issue in issues:
        print("-", issue)
