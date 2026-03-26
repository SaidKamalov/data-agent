---
name: data-collection
description: Search and download text classification datasets from Kaggle, HuggingFace, and web sources
metadata:
  pipeline-stage: collection
---

# Data Collection Skill

Search and download text classification datasets from Kaggle, HuggingFace, and web sources.

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

## IMPORTANT: Tool Usage Rules

- **Use the `question` tool to present options and get user input.** Do NOT use bash `echo`/`cat`/`printf` to print options — the user cannot respond to bash output.
- **Maximum 3 search queries total.** Run 2 queries initially (one per source). Only run a 3rd if results are insufficient.
- **Always run at least one websearch call** to discover alternative data sources beyond Kaggle and HuggingFace.
- **After each `question` call, STOP and WAIT** for the user to respond before proceeding.

## Workflow (follow exactly, in order)

### Step 1: Parse contract
Read the `DataContract` JSON from the session workspace to understand what data the user needs.

### Step 2: Search sources (max 3 queries)
Run search scripts for each source in `sources_preference`. Use the contract `topic` as the query. Append "text classification" or "sentiment" to improve relevance for text tasks:
```bash
uv run scripts/search_kaggle.py --query "<contract.topic> text classification dataset" --max-results 10
uv run scripts/search_huggingface.py --query "<contract.topic> classification" --max-results 10
```
If total relevant results are fewer than 3, try ONE additional broader query. Then STOP searching.

### Step 3: Websearch for alternative sources
Run at least one websearch call to find datasets outside Kaggle/HuggingFace:
```
websearch(query="<topic> dataset download csv")
```
From the results, extract 2-3 relevant data source URLs with their descriptions. Add these to the pool of options alongside Kaggle/HF results.

### Step 4: Compile, filter, and order results
Combine all results (Kaggle + HuggingFace + websearch). Order by relevance to the user's query, regardless of source. Filter by `format_preference` and `size_preference`. Prefer datasets that mention having a clear text column and label/class column in their description. Keep top 5-6 most relevant.

### Step 5: Call `question` tool to present options
**Call the `question` tool** (NOT bash) to present found datasets and ask the user which one(s) to download. Order options by relevance, prefix with source type:
```
question(questions=[{
  "question": "I found these datasets matching your requirements. Which one would you like to download?",
  "header": "Select dataset",
  "options": [
    {"label": "Option 1 (web)", "description": "direct download, format, brief description"},
    {"label": "Option 2 (Kaggle)", "description": "Kaggle, size, brief description"},
    {"label": "Option 3 (HF)", "description": "HuggingFace, size, brief description"},
    ...
  ]
}])
```
WAIT for the user response. Do NOT proceed until the user selects an option.

### Step 6: Download selected dataset
Run the appropriate download script based on the selected source:

**For Kaggle:**
```bash
uv run scripts/download_kaggle.py --dataset-id "<selected_slug>" --output "<session_dir>/collection/data/"
```

**For HuggingFace:**
```bash
uv run scripts/download_huggingface.py --dataset-id "<selected_id>" --output "<session_dir>/collection/data/"
```

**For web sources:**
Read `template_scrape_web.py` or `template_call_api.py` as reference patterns. Write a temporary script adapted to the specific URL, execute via `uv run`, and save output to `<session_dir>/collection/data/`.

### Step 7: Call `question` tool to confirm
**Call the `question` tool** (NOT bash) to confirm the downloaded dataset looks correct and ask about format conversion:
```
question(questions=[{
  "question": "Dataset downloaded to <path>. Would you like to convert the format?",
  "header": "Format conversion",
  "options": [
    {"label": "Keep as-is", "description": "No conversion needed"},
    {"label": "Convert to CSV", "description": "Convert all files to CSV format"},
    {"label": "Convert to JSON", "description": "Convert all files to JSON format"}
  ]
}])
```
WAIT for the user response before proceeding.

### Step 8: Write report
Write `report.md` in `<session_dir>/collection/` summarizing:
- Sources searched (Kaggle, HuggingFace, websearch) and number of results per source
- Selected dataset details
- Downloaded files and their sizes
- Any issues encountered

### Step 9: Return summary
Return a text summary to the orchestrator. This is your FINAL action — do not loop back.

## Environment Requirements

- `KAGGLE_USERNAME` and `KAGGLE_API_TOKEN` — for Kaggle search/download
- `HUGGINGFACE_TOKEN` — for HuggingFace search/download (optional for public datasets)

All set in `.env` file at project root.
