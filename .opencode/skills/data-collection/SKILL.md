---
name: data-collection
description: Search and download datasets from Kaggle, HuggingFace, and web sources
metadata:
  pipeline-stage: collection
---

# Data Collection Skill

Search and download datasets from Kaggle, HuggingFace, and web sources.

## Available Scripts

All scripts are in `.opencode/skills/data-collection/scripts/`.

### Search Scripts

```bash
# Search Kaggle datasets
uv run .opencode/skills/data-collection/scripts/search_kaggle.py --query "climate data" --max-results 10

# Search HuggingFace datasets
uv run .opencode/skills/data-collection/scripts/search_huggingface.py --query "climate data" --max-results 10
```

Both output a JSON array of `DatasetOption` objects to stdout.

### Download Scripts

```bash
# Download from Kaggle (owner/dataset-slug)
uv run .opencode/skills/data-collection/scripts/download_kaggle.py --dataset-id owner/dataset-name --output workspace/session-.../collection/data/

# Download from HuggingFace
uv run .opencode/skills/data-collection/scripts/download_huggingface.py --dataset-id username/dataset-name --output workspace/session-.../collection/data/
```

Both output a JSON object with download status and file paths to stdout.

### Templates (agent reference)

- `template_scrape_web.py` — `requests-html` pattern for web scraping
- `template_call_api.py` — `requests` pattern for REST API calls

These are code templates, not runnable scripts. The agent adapts and executes its own versions.

## Workflow

1. **Parse contract** — Read the `DataContract` JSON from the session workspace to understand what data the user needs.

2. **Search sources** — Run search scripts for each source in `sources_preference`:
   ```bash
   uv run scripts/search_kaggle.py --query "<contract.topic>" --max-results 10
   uv run scripts/search_huggingface.py --query "<contract.topic>" --max-results 10
   ```

3. **Compile results** — Collect all `DatasetOption` results into a single list. Filter by format if `format_preference` is set.

4. **DECISION POINT 1: Present options to user**
   Use the `question` tool to present found datasets and ask the user which one(s) to download:
   ```
   question(
     questions=[{
       "question": "I found these datasets matching your requirements. Which one would you like to download?",
       "header": "Select dataset",
       "options": [
         {"label": "Option 1 name", "description": "source, size, format"},
         {"label": "Option 2 name", "description": "source, size, format"},
         ...
       ]
     }]
   )
   ```

5. **Download selected dataset** — Run the appropriate download script:
   ```bash
   uv run scripts/download_kaggle.py --dataset-id "<selected_slug>" --output "<session_dir>/collection/data/"
   # or
   uv run scripts/download_huggingface.py --dataset-id "<selected_id>" --output "<session_dir>/collection/data/"
   ```

6. **DECISION POINT 2: Confirm dataset**
   Use the `question` tool to confirm the downloaded dataset looks correct and ask about format conversion:
   ```
   question(
     questions=[{
       "question": "Dataset downloaded to <path>. Would you like to convert the format?",
       "header": "Format conversion",
       "options": [
         {"label": "Keep as-is", "description": "No conversion needed"},
         {"label": "Convert to CSV", "description": "Convert all files to CSV format"},
         {"label": "Convert to JSON", "description": "Convert all files to JSON format"}
       ]
     }]
   )
   ```

7. **Write report** — Write `report.md` in `<session_dir>/collection/` summarizing:
   - Sources searched and number of results per source
   - Selected dataset details
   - Downloaded files and their sizes
   - Any issues encountered

8. **Return summary** — Return a text summary to the orchestrator.

## Environment Requirements

- `KAGGLE_USERNAME` and `KAGGLE_API_TOKEN` — for Kaggle search/download
- `HUGGINGFACE_TOKEN` — for HuggingFace search/download (optional for public datasets)

All set in `.env` file at project root.
