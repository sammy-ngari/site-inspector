from scanner import basic_check, security_headers, ssl_check, detect_cms
from report import print_report

domain = input("Enter a domain to scan (e.g., example.com): ")

basic = basic_check(domain)

if not basic["reachable"]:
    print("Could not reach website")
    exit()

ssl_data = ssl_check(domain.replace("https://", "").replace("http://", "").split("/")[0])
headers = security_headers(basic["headers"])
cms = detect_cms(basic["content"])

print_report(domain, basic, ssl_data, headers, cms)