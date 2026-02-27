"""
Networking utilities.

Provides a single HTTP retrieval function used by the scanner layer.
All higher-level analysis relies on the structured response returned here.
"""

import requests

def fetch_site(url):

    """
    Execute an HTTP GET request and return structured response data.

    Parameters
    ----------
    url : str
        Domain or URL provided by the caller.

    Returns
    -------
    dict | None
        {
            "url": str,              # Final resolved URL
            "status_code": int,      # HTTP status code
            "headers": Mapping,      # Response headers
            "content": str,          # Response body (text)
            "size": int,             # Raw payload size in bytes
            "history": list          # Redirect history
        }

        Returns None if the request fails.
    """
    
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