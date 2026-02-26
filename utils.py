import requests

def fetch_site(url):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        return{
            "url": response.url,
            "status_code": response.status_code,
            "headers": response.headers,
            "content": response.text,
            "size": len(response.content),
            "history": response.history
        }
    
    except requests.exceptions.RequestException:
        return