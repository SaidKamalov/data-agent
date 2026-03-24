"""Template: REST API calls with requests.

This is a reference template — not a runnable CLI script.
The agent should adapt this pattern when calling REST APIs to fetch data.
"""

# --- Pattern: basic GET request with params ---
import requests

base_url = "https://api.example.com/v1/datasets"
params = {
    "query": "climate data",
    "limit": 10,
    "offset": 0,
}

response = requests.get(base_url, params=params, timeout=30)
response.raise_for_status()
data = response.json()

# --- Pattern: authenticated API calls ---
headers = {
    "Authorization": "Bearer YOUR_TOKEN_HERE",
    "Accept": "application/json",
}

response = requests.get(base_url, headers=headers, params=params, timeout=30)
response.raise_for_status()


# --- Pattern: paginated data fetching ---
def fetch_all_pages(base_url: str, params: dict, page_size: int = 100) -> list[dict]:
    """Fetch all pages from a paginated API endpoint.

    Args:
        base_url: API endpoint URL.
        params: Query parameters (will add/override pagination params).
        page_size: Number of items per page.

    Returns:
        Combined list of all items across all pages.
    """
    all_items = []
    offset = 0

    while True:
        page_params = {**params, "limit": page_size, "offset": offset}
        response = requests.get(base_url, params=page_params, timeout=30)
        response.raise_for_status()

        result = response.json()
        items = result.get("results", result.get("data", []))

        if not items:
            break

        all_items.extend(items)
        offset += page_size

        # Check if we've reached the end
        if len(items) < page_size:
            break

    return all_items


# --- Pattern: POST request for search/filter ---
search_payload = {
    "filters": {
        "domain": "finance",
        "format": "csv",
        "min_size": 1000,
    },
    "sort_by": "relevance",
    "limit": 20,
}

response = requests.post(
    f"{base_url}/search",
    json=search_payload,
    headers=headers,
    timeout=30,
)
response.raise_for_status()
results = response.json()


# --- Pattern: downloading files from API ---
def download_file(url: str, output_path: str, headers: dict | None = None) -> str:
    """Download a file from a URL and save it locally.

    Args:
        url: URL to download from.
        output_path: Local path to save the file.
        headers: Optional request headers.

    Returns:
        Path to the downloaded file.
    """
    from pathlib import Path

    response = requests.get(url, headers=headers, timeout=120, stream=True)
    response.raise_for_status()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return output_path


# --- Pattern: error handling with retries ---
from requests.adapters import HTTPAdapter  # noqa: E402
from urllib3.util.retry import Retry  # noqa: E402

session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

try:
    response = session.get(base_url, params=params, timeout=30)
    response.raise_for_status()
except requests.HTTPError as e:
    print(f"HTTP error: {e.response.status_code} - {e.response.text}")
    raise
except requests.RequestException as e:
    print(f"Request failed: {e}")
    raise
