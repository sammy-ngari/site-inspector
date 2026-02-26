from risk import analyze_risk

def print_report(domain, basic, ssl_data, headers, cms):

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

    print("\n--- Risk Analysis ---")
    level, issues = analyze_risk(basic, ssl_data, headers, cms)
    print("OverallRisk Level:", level)
    for issue in issues:
        print("-", issue)
