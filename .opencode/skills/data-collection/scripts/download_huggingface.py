"""Download a dataset from HuggingFace Hub."""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def download_huggingface(dataset_id: str, output_dir: str) -> dict:
    """Download a HuggingFace dataset via snapshot_download.

    Args:
        dataset_id: HuggingFace dataset repository ID (e.g., 'username/dataset-name').
        output_dir: Local directory to store the downloaded dataset.

    Returns:
        Dict with download status and list of file paths.
    """
    from huggingface_hub import snapshot_download

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    token = os.getenv("HUGGINGFACE_TOKEN")

    snapshot_download(
        repo_id=dataset_id,
        repo_type="dataset",
        local_dir=str(output_path),
        token=token or None,
    )

    # Collect all downloaded files
    downloaded_files = sorted(str(p) for p in output_path.rglob("*") if p.is_file())
    return {
        "status": "success",
        "dataset_id": dataset_id,
        "output_dir": str(output_path),
        "files": downloaded_files,
    }


def main() -> None:
    """CLI entry point for HuggingFace dataset download."""
    parser = argparse.ArgumentParser(description="Download a HuggingFace dataset.")
    parser.add_argument(
        "--dataset-id", required=True, help="HuggingFace dataset repo ID"
    )
    parser.add_argument(
        "--output", required=True, help="Output directory for downloaded files"
    )
    args = parser.parse_args()

    load_dotenv()

    try:
        result = download_huggingface(args.dataset_id, args.output)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error downloading from HuggingFace: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
