"""Download a dataset from Kaggle by slug."""

import argparse
import io
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def download_kaggle(dataset_id: str, output_dir: str, file: str | None = None) -> dict:
    """Download a Kaggle dataset by its owner/slug identifier.

    Args:
        dataset_id: Kaggle dataset slug (owner/dataset-name).
        output_dir: Directory to download files into.
        file: Optional specific file to download from the dataset.

    Returns:
        Dict with download status and list of file paths.
    """
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Suppress Kaggle API's stdout output (e.g., "Dataset URL: ...")
    _stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        api.dataset_download_files(
            dataset=dataset_id,
            path=str(output_path),
            force=True,
            quiet=True,
            unzip=True,
        )
    finally:
        sys.stdout = _stdout

    # Collect all downloaded files
    downloaded_files = sorted(str(p) for p in output_path.rglob("*") if p.is_file())
    return {
        "status": "success",
        "dataset_id": dataset_id,
        "output_dir": str(output_path),
        "files": downloaded_files,
    }


def main() -> None:
    """CLI entry point for Kaggle dataset download."""
    parser = argparse.ArgumentParser(description="Download a Kaggle dataset.")
    parser.add_argument(
        "--dataset-id", required=True, help="Kaggle dataset slug (owner/dataset-name)"
    )
    parser.add_argument(
        "--output", required=True, help="Output directory for downloaded files"
    )
    parser.add_argument(
        "--file", default=None, help="Specific file to download (optional)"
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

    os.environ["KAGGLE_USERNAME"] = kaggle_username
    os.environ["KAGGLE_KEY"] = kaggle_token

    try:
        result = download_kaggle(args.dataset_id, args.output, args.file)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error downloading from Kaggle: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
