"""
Networking utilities.

Provides a single HTTP retrieval function used by the scanner layer.
All higher-level analysis relies on the structured response returned here.
"""

from urllib.parse import urlparse

import requests

REQUEST_TIMEOUT_SECONDS = 10


def normalize_url(url):
    """
    Normalize user input into a URL suitable for passive inspection.
    """

    cleaned_url = url.strip()

    if not cleaned_url.startswith("http://") and not cleaned_url.startswith("https://"):
        return "https://" + cleaned_url

    return cleaned_url


def extract_hostname(url):
    """
    Extract a hostname from a domain or URL string.
    """

    parsed_url = urlparse(normalize_url(url))
    return parsed_url.hostname


def _serialize_redirect_history(history):
    """
    Convert redirect responses into JSON-safe metadata.
    """

    serialized_history = []

    for response in history:
        serialized_history.append(
            {
                "url": response.url,
                "status_code": response.status_code,
                "location": response.headers.get("Location"),
            }
        )

    return serialized_history


def fetch_site(url):
    """
    Execute an HTTP GET request and return structured response data.

    Parameters
    ----------
    url : str
        Domain or URL provided by the caller.

    Returns
    -------
    dict
        {
            "ok": bool,
            "requested_url": str,
            "normalized_url": str,
            "url": str,              # Final resolved URL
            "status_code": int,      # HTTP status code
            "headers": dict,         # Response headers
            "content": str,          # Response body (text)
            "size": int,             # Raw payload size in bytes
            "history": list          # Redirect history
        }
    """

    normalized_url = normalize_url(url)

    try:
        response = requests.get(
            normalized_url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
        )
        return {
            "ok": True,
            "requested_url": url,
            "normalized_url": normalized_url,
            "url": response.url,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.text,
            "size": len(response.content),
            "history": _serialize_redirect_history(response.history),
        }

    except requests.exceptions.RequestException as exc:
        return {
            "ok": False,
            "requested_url": url,
            "normalized_url": normalized_url,
            "error": str(exc),
            "error_type": exc.__class__.__name__,
        }
