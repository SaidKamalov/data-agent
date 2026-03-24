"""Template: Web scraping with requests-html.

This is a reference template — not a runnable CLI script.
The agent should adapt this pattern when scraping web-based data sources.
"""

# --- Pattern: basic HTML session and page fetch ---
from requests_html import HTMLSession

# Create a session (persistent across requests)
session = HTMLSession()

# Fetch a page
url = "https://example.com/data-page"
r = session.get(url)

# --- Pattern: finding elements by CSS selector ---
# Find all elements matching a CSS selector
elements = r.html.find("table.data-table")

for element in elements:
    # Access text content
    text = element.text
    # Access attributes
    attrs = element.attrs
    # Access inner HTML
    html = element.html

# --- Pattern: extracting tabular data from HTML tables ---
tables = r.html.find("table")

for table in tables:
    # Get all rows
    rows = table.find("tr")
    for row in rows:
        # Get all cells in the row
        cells = row.find("td") or row.find("th")
        cell_texts = [cell.text.strip() for cell in cells]
        print(cell_texts)

# --- Pattern: extracting links ---
links = r.html.find("a")
for link in links:
    href = link.attrs.get("href", "")
    text = link.text.strip()
    print(f"{text}: {href}")

# --- Pattern: handling JavaScript-rendered content ---
# Some pages require JavaScript execution to load data
r.html.render(sleep=2, timeout=10)

# After render(), re-find elements
dynamic_elements = r.html.find(".dynamic-content")


# --- Pattern: pagination ---
def scrape_all_pages(start_url: str, next_selector: str) -> list[dict]:
    """Scrape all pages following 'next' links.

    Args:
        start_url: URL of the first page.
        next_selector: CSS selector for the 'next page' link.

    Returns:
        List of scraped data dicts from all pages.
    """
    results = []
    current_url = start_url
    session = HTMLSession()

    while current_url:
        r = session.get(current_url)
        # ... extract data from current page ...
        # results.extend(extract_data(r))

        # Find next page link
        next_links = r.html.find(next_selector)
        if next_links:
            href = next_links[0].attrs.get("href", "")
            current_url = (
                href if href.startswith("http") else None
            )  # Resolve relative URLs
        else:
            current_url = None

    return results


# --- Pattern: error handling ---
import requests  # noqa: E402

try:
    r = session.get(url, timeout=30)
    r.raise_for_status()
except requests.RequestException as e:
    print(f"Request failed: {e}")
    raise
