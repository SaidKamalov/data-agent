"""Integration tests for data collection helper scripts.

Tests run the scripts via subprocess and validate their JSON output format.
Test artifacts are stored in test_data-collection-session/ and cleaned up at the end.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv()

SCRIPTS_DIR = (
    Path(__file__).parent.parent
    / ".opencode"
    / "skills"
    / "data-collection"
    / "scripts"
)
SESSION_DIR = Path(__file__).parent / "test_data-collection-session"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_script(
    script_name: str, args: list[str], timeout: int = 60
) -> subprocess.CompletedProcess:
    """Run a helper script via uv and return the result."""
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name), *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _assert_valid_dataset_options(items: list[dict]) -> None:
    """Validate that each item matches the DatasetOption schema."""
    required_keys = {"name", "description", "source", "url", "download_id"}
    for item in items:
        for key in required_keys:
            assert key in item, f"Missing key '{key}' in {item}"
        assert isinstance(item["name"], str) and len(item["name"]) > 0
        assert isinstance(item["description"], str)
        assert item["source"] in ("kaggle", "huggingface", "web")
        assert item["url"].startswith("http")


def _assert_download_result(result: dict) -> None:
    """Validate download result structure."""
    assert result["status"] == "success"
    assert "dataset_id" in result
    assert "output_dir" in result
    assert "files" in result
    assert isinstance(result["files"], list)


# ---------------------------------------------------------------------------
# Kaggle tests (skip if credentials not configured)
# ---------------------------------------------------------------------------

_has_kaggle_creds = bool(os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_API_TOKEN"))


@pytest.mark.skipif(not _has_kaggle_creds, reason="Kaggle credentials not configured")
class TestKaggleSearch:
    """Test search_kaggle.py via CLI."""

    def test_search_returns_json_array(self) -> None:
        """Search should return a JSON array of DatasetOption objects."""
        result = _run_script(
            "search_kaggle.py", ["--query", "iris", "--max-results", "3"]
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) <= 3

    def test_search_output_matches_schema(self) -> None:
        """Each result should match the DatasetOption schema."""
        result = _run_script(
            "search_kaggle.py", ["--query", "titanic", "--max-results", "5"]
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        data = json.loads(result.stdout)
        _assert_valid_dataset_options(data)

    def test_search_source_is_kaggle(self) -> None:
        """All results should have source='kaggle'."""
        result = _run_script(
            "search_kaggle.py", ["--query", "pokemon", "--max-results", "2"]
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        data = json.loads(result.stdout)
        for item in data:
            assert item["source"] == "kaggle"

    def test_search_fails_without_query(self) -> None:
        """Missing --query should cause non-zero exit."""
        result = _run_script("search_kaggle.py", [])
        assert result.returncode != 0


@pytest.mark.skipif(not _has_kaggle_creds, reason="Kaggle credentials not configured")
class TestKaggleDownload:
    """Test download_kaggle.py via CLI."""

    def test_download_creates_files(self) -> None:
        """Downloading a small dataset should produce files on disk."""
        out_dir = str(SESSION_DIR / "kaggle")
        result = _run_script(
            "download_kaggle.py",
            ["--dataset-id", "heptapod/titanic", "--output", out_dir],
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        data = json.loads(result.stdout)
        _assert_download_result(data)
        assert len(data["files"]) > 0
        for f in data["files"]:
            assert Path(f).exists()

    def test_download_output_json(self) -> None:
        """Output should be valid JSON with expected keys."""
        out_dir = str(SESSION_DIR / "kaggle_json")
        result = _run_script(
            "download_kaggle.py",
            ["--dataset-id", "heptapod/titanic", "--output", out_dir],
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        data = json.loads(result.stdout)
        assert data["dataset_id"] == "heptapod/titanic"


# ---------------------------------------------------------------------------
# HuggingFace tests
# ---------------------------------------------------------------------------


class TestHuggingFaceSearch:
    """Test search_huggingface.py via CLI."""

    def test_search_returns_json_array(self) -> None:
        """Search should return a JSON array."""
        result = _run_script(
            "search_huggingface.py", ["--query", "imdb", "--max-results", "3"]
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0
        assert len(data) <= 3

    def test_search_output_matches_schema(self) -> None:
        """Each result should match the DatasetOption schema."""
        result = _run_script(
            "search_huggingface.py", ["--query", "squad", "--max-results", "5"]
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        data = json.loads(result.stdout)
        _assert_valid_dataset_options(data)

    def test_search_source_is_huggingface(self) -> None:
        """All results should have source='huggingface'."""
        result = _run_script(
            "search_huggingface.py", ["--query", "mnist", "--max-results", "2"]
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        data = json.loads(result.stdout)
        for item in data:
            assert item["source"] == "huggingface"

    def test_search_max_results_respected(self) -> None:
        """Should return at most max-results items."""
        result = _run_script(
            "search_huggingface.py", ["--query", "text", "--max-results", "2"]
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        data = json.loads(result.stdout)
        assert len(data) <= 2

    def test_search_fails_without_query(self) -> None:
        """Missing --query should cause non-zero exit."""
        result = _run_script("search_huggingface.py", [])
        assert result.returncode != 0


class TestHuggingFaceDownload:
    """Test download_huggingface.py via CLI."""

    def test_download_creates_files(self) -> None:
        """Downloading a small dataset should produce files on disk."""
        out_dir = str(SESSION_DIR / "huggingface")
        result = _run_script(
            "download_huggingface.py",
            ["--dataset-id", "stanfordnlp/imdb", "--output", out_dir],
            timeout=180,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        data = json.loads(result.stdout)
        _assert_download_result(data)
        assert len(data["files"]) > 0
        for f in data["files"]:
            assert Path(f).exists()

    def test_download_output_json(self) -> None:
        """Output should be valid JSON with expected keys."""
        out_dir = str(SESSION_DIR / "huggingface_json")
        result = _run_script(
            "download_huggingface.py",
            ["--dataset-id", "stanfordnlp/imdb", "--output", out_dir],
            timeout=180,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        data = json.loads(result.stdout)
        assert data["dataset_id"] == "stanfordnlp/imdb"
        assert data["status"] == "success"


# ---------------------------------------------------------------------------
# Web scraping test (adapted from template_scrape_web.py)
# ---------------------------------------------------------------------------


class TestWebScraping:
    """Test web scraping pattern using requests-html on a static page."""

    def test_scrape_static_table(self) -> None:
        """Scrape a table from a static HTML page."""
        from requests_html import HTMLSession

        session = HTMLSession()
        url = "https://www.w3schools.com/html/html_tables.asp"
        r = session.get(url)
        assert r.status_code == 200

        tables = r.html.find("table")
        assert len(tables) > 0, "Expected at least one table on the page"

        # Extract rows from the first table
        rows = tables[0].find("tr")
        assert len(rows) > 1, "Expected multiple rows in the table"

        # Verify we can extract cell text
        for row in rows[:3]:
            cells = row.find("th") or row.find("td")
            texts = [c.text.strip() for c in cells]
            assert len(texts) > 0, "Each row should have at least one cell"

    def test_scrape_links(self) -> None:
        """Verify we can extract links from a static page."""
        from requests_html import HTMLSession

        session = HTMLSession()
        url = "https://httpbin.org/links/10"
        r = session.get(url)
        assert r.status_code == 200

        links = r.html.find("a")
        assert len(links) >= 9
        for link in links:
            href = link.attrs.get("href", "")
            assert href, "Each link should have an href"


# ---------------------------------------------------------------------------
# API call test (adapted from template_call_api.py)
# ---------------------------------------------------------------------------


class TestApiCalls:
    """Test REST API call pattern using a public free API."""

    def test_get_request_json(self) -> None:
        """GET request to jsonplaceholder should return valid JSON."""
        import requests

        resp = requests.get("https://jsonplaceholder.typicode.com/posts/1", timeout=15)
        assert resp.status_code == 200
        data = resp.json()
        assert "userId" in data
        assert "title" in data
        assert "body" in data

    def test_get_with_params(self) -> None:
        """GET with query params should filter results."""
        import requests

        resp = requests.get(
            "https://jsonplaceholder.typicode.com/posts",
            params={"userId": 1},
            timeout=15,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for post in data:
            assert post["userId"] == 1

    def test_pagination_pattern(self) -> None:
        """Paginated fetching should accumulate items correctly."""
        import requests

        base_url = "https://jsonplaceholder.typicode.com/posts"
        all_items = []
        page_size = 10
        offset = 0

        while True:
            resp = requests.get(
                base_url, params={"_start": offset, "_limit": page_size}, timeout=15
            )
            assert resp.status_code == 200
            items = resp.json()
            if not items:
                break
            all_items.extend(items)
            offset += page_size
            if len(items) < page_size:
                break

        assert len(all_items) == 100  # jsonplaceholder has exactly 100 posts

    def test_request_error_handling(self) -> None:
        """HTTP errors should be handled gracefully."""
        import requests

        resp = requests.get(
            "https://jsonplaceholder.typicode.com/nonexistent", timeout=15
        )
        assert resp.status_code == 404

        with pytest.raises(requests.HTTPError):
            resp.raise_for_status()


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def cleanup_session_dir() -> None:
    """Remove test_data-collection-session/ after all tests finish."""
    yield
    if SESSION_DIR.exists():
        shutil.rmtree(SESSION_DIR)
