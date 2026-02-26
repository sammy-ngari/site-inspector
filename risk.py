def analyze_risk(basic, ssl_data, headers, cms):
    issues = []
    score = 0 

    #SSL
    if not ssl_data["Valid"]:
        issues.append("No valid SSL certificate (users may see security warnings)")
        score += 4
    elif ssl_data["Days Left"] < 30:
        issues.append(f"SSL certificate expiring soon (in {ssl_data['Days Left']} days)")
        score += 3

    #Response Time
    if basic["response_time"] > 2:
        issues.append(f"Slow response time ({basic['response_time']} seconds). Possible hosting or optimization issue")
        score += 2

    #Redirects
    if basic["redirects"] == 0:
        issues.append("HTTPS redirect may not be enforced (users may access insecure version)")
        score += 2

    #Security Headers
    if headers["CSP"] == "Missing":
        issues.append("Missing Content-Security-Policy header (increased risk of XSS attacks)")
        score += 2

    if headers["HSTS"] == "Missing":
        issues.append("Missing Strict-Transport-Security header (connections may downgrade to HTTP)")
        score += 2

    if headers["X-Content-Type-Options"] == "Missing":
        issues.append("Missing X-Content-Type-Options header (increased risk of MIME type confusion attacks)")
        score += 2

    if headers["X-Frame-Options"] == "Missing":
        issues.append("Missing X-Frame-Options header (increased risk of clickjacking attacks)")
        score += 2

    if headers["Referrer-Policy"] == "Missing":
        issues.append("Missing Referrer-Policy header (potential information leakage through referrer)")
        score += 2

    #WordPress specific
    if cms == "WordPress":
        issues.append("Site is running WordPress (common target for attacks, ensure it's updated)")
    
    #Risk Level
    if score >= 7:
        level = "High"
    elif score >= 4:
        level = "Medium"
    else:
        level = "Low"

    return level, issues