"""Search HuggingFace Hub for datasets matching a query."""

import argparse
import json
import sys

from dotenv import load_dotenv


def search_huggingface(query: str, max_results: int = 10) -> list[dict]:
    """Search HuggingFace Hub datasets via the official API.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return.

    Returns:
        List of dataset dicts matching the DatasetOption schema.
    """
    from huggingface_hub import HfApi

    api = HfApi()

    datasets = list(
        api.list_datasets(search=query, limit=max_results, sort="downloads")
    )

    results = []
    for ds in datasets:
        tags = ds.tags or []
        # Try to extract format from tags
        fmt = None
        for tag in tags:
            if tag.startswith("format:"):
                fmt = tag.split(":", 1)[1]
                break

        results.append(
            {
                "name": ds.id,
                "description": ds.description or ds.id,
                "source": "huggingface",
                "size": None,
                "format": fmt,
                "url": f"https://huggingface.co/datasets/{ds.id}",
                "download_id": ds.id,
            }
        )
    return results


def main() -> None:
    """CLI entry point for HuggingFace dataset search."""
    parser = argparse.ArgumentParser(description="Search HuggingFace Hub for datasets.")
    parser.add_argument("--query", required=True, help="Search query string")
    parser.add_argument(
        "--max-results", type=int, default=10, help="Maximum results to return"
    )
    args = parser.parse_args()

    load_dotenv()

    try:
        results = search_huggingface(args.query, args.max_results)
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error searching HuggingFace: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
