import requests
import cbor
import time
from utils.response import Response
from urllib.parse import urlparse

def download(url, config, logger=None):
    host, port = config.cache_server
    resp = requests.get(
        f"http://{host}:{port}/",
        params=[("q", f"{url}"), ("u", f"{config.user_agent}")])
    try:
        if resp and resp.content:
            return Response(cbor.loads(resp.content))
    except (EOFError, ValueError) as e:
        pass
    logger.error(f"Spacetime Response error {resp} with url {url}.")
    return Response({
        "error": f"Spacetime Response error {resp} with url {url}.",
        "status": resp.status_code,
        "url": url})

def download_robots_txt(url):
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

    try:
        response = requests.get(robots_url)

        if response.status_code == 200:
            return Response({"robots_txt": response.text, "status": response.status_code, "url": robots_url})
        else:
            error_message = f"Failed to fetch robots.txt: HTTP {response.status_code}"
            return Response({"error": error_message, "status": response.status_code, "url": robots_url})

    except requests.exceptions.RequestException as e:
        error_message = f"Error fetching robots.txt from {robots_url}: {e}"
        return Response({"error": error_message, "status": "error", "url": robots_url})