"""Search Kaggle for datasets matching a query."""

import argparse
import json
import os
import sys

from dotenv import load_dotenv


def search_kaggle(query: str, max_results: int = 10) -> list[dict]:
    """Search Kaggle datasets via the official API.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return.

    Returns:
        List of dataset dicts matching the DatasetOption schema.
    """
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    datasets = api.dataset_list(
        search=query, max_size=None, file_type=None, sort_by="hottest"
    )
    results = []
    for ds in datasets[:max_results]:
        slug = f"{ds.ref}"
        results.append(
            {
                "name": ds.title,
                "description": ds.subtitle or "",
                "source": "kaggle",
                "size": _format_size(ds.total_bytes) if ds.total_bytes else None,
                "format": None,
                "url": f"https://www.kaggle.com/datasets/{slug}",
                "download_id": slug,
            }
        )
    return results


def _format_size(size_bytes: int) -> str:
    """Convert bytes to human-readable size string.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Human-readable size string.
    """
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def main() -> None:
    """CLI entry point for Kaggle dataset search."""
    parser = argparse.ArgumentParser(description="Search Kaggle for datasets.")
    parser.add_argument("--query", required=True, help="Search query string")
    parser.add_argument(
        "--max-results", type=int, default=10, help="Maximum results to return"
    )
    parser.add_argument(
        "--format", default=None, help="Filter by file format (csv, json, etc.)"
    )
    args = parser.parse_args()

    load_dotenv()

    kaggle_username = os.getenv("KAGGLE_USERNAME")
    kaggle_token = os.getenv("KAGGLE_API_TOKEN")
    if not kaggle_username or not kaggle_token:
        print(
            "Error: KAGGLE_USERNAME and KAGGLE_API_TOKEN must be set in .env",
            file=sys.stderr,
        )
        sys.exit(1)

    # Set env vars that kaggle API expects
    os.environ["KAGGLE_USERNAME"] = kaggle_username
    os.environ["KAGGLE_KEY"] = kaggle_token

    try:
        results = search_kaggle(args.query, args.max_results)
        if args.format:
            results = [
                r for r in results if r.get("format", "").lower() == args.format.lower()
            ]
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error searching Kaggle: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
