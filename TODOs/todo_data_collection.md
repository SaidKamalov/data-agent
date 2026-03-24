# TODO: Data Collection Agent

## Overview

Implement the first pipeline stage — data collection. This includes data models, 6 helper scripts, a skill definition, and an agent definition.

## Files to create/modify (10 total)

### 1. Config file updates

| File | Change |
|---|---|
| `.env_example` | Add `KAGGLE_API_TOKEN=`, `KAGGLE_USERNAME=`, `HUGGINGFACE_TOKEN=` |
| `pyproject.toml` | Add `kaggle`, `huggingface_hub`, `requests`, `requests-html`, `python-dotenv`, `pydantic` to dependencies |
| `.gitignore` | Add `.env`, `workspace/` |

### 2. `src/models.py` — Data models

Two Pydantic models:

```python
class DatasetOption(BaseModel):
    name: str
    description: str
    source: str  # "kaggle" | "huggingface" | "web"
    size: str | None
    format: str | None
    url: str
    download_id: str  # kaggle slug or HF dataset id

class DataContract(BaseModel):
    topic: str
    domain: str
    timeframe: str
    sources_preference: list[str]
    format_preference: str
    size_preference: str
    columns_of_interest: list[str]
    quality_requirements: str
    annotation_task: str
    annotation_labels: list[str]
```

### 3. Scripts (6 files in `.opencode/skills/data-collection/scripts/`)

#### `search_kaggle.py` — Full CLI script
- Uses `kaggle.api.dataset_list(search_query=...)` via Python API
- Args: `--query`, `--max-results`, `--format`
- Outputs JSON array of `DatasetOption` objects to stdout
- Loads `KAGGLE_USERNAME` and `KAGGLE_API_TOKEN` from `.env`

#### `download_kaggle.py` — Full CLI script
- Uses `kaggle.api.dataset_download_files(slug, path, unzip=True)`
- Args: `--dataset-id` (owner/slug), `--output`, `--file` (optional specific file)
- Outputs JSON with download status and file paths to stdout

#### `search_huggingface.py` — Full CLI script
- Uses `HfApi().list_datasets(search=query, limit=N, sort="downloads")`
- Args: `--query`, `--max-results`
- Extracts `id`, `description`, `downloads`, `tags`, `last_modified`
- Outputs JSON array of `DatasetOption` objects to stdout

#### `download_huggingface.py` — Full CLI script
- Uses `snapshot_download(repo_id=dataset_id, repo_type="dataset", local_dir=output)`
- Args: `--dataset-id`, `--output`
- Outputs JSON with download status and file paths to stdout

#### `template_scrape_web.py` — Template/snippet
- Demonstrates `requests-html` pattern: `HTMLSession()`, `session.get(url)`, `r.html.find(selector)`, table extraction
- Heavily commented, meant as agent reference — agent adapts and executes its own version
- Not a runnable CLI script — a code template

#### `template_call_api.py` — Template/snippet
- Demonstrates `requests` pattern: `requests.get(url, params=...)`, JSON parsing, error handling, pagination
- Heavily commented, meant as agent reference — agent adapts and executes its own version
- Not a runnable CLI script — a code template

All full scripts follow conventions from PROJECT_SPEC.md:
- Accept CLI arguments via `argparse`
- Print results to stdout as JSON (for machine consumption)
- Exit code 0 on success, non-zero on failure
- No interactive prompts (all config via CLI args)
- Use `load_dotenv()` at top, `os.getenv()` for credentials
- Fail early with clear error if required env var is missing
- Type hints on all function signatures
- Concise docstrings on every function and module

### 4. `.opencode/skills/data-collection/SKILL.md`

Frontmatter:
```yaml
name: data-collection
description: Search and download datasets from Kaggle, HuggingFace, and web sources
metadata:
  pipeline-stage: collection
```

Body contains:
- Available scripts with CLI usage examples
- Workflow steps
- **DECISION POINT 1**: After search — present found datasets via `question` tool, ask user to pick
- **DECISION POINT 2**: After download — confirm dataset looks correct, ask about format conversion

### 5. `.opencode/agents/data-collection.md`

Frontmatter:
```yaml
description: Searches and downloads datasets from Kaggle, HuggingFace, and web sources
mode: subagent
temperature: 0.1
permission:
  bash:
    "*": allow
  edit: deny
```

Body: agent instructions — load skill, run searches, present options, download, write report.md, return summary.

## Execution order

1. `pyproject.toml`, `.gitignore`, `.env_example` — config baseline.
Update pyproject.toml only through uv package manager!
2. `src/models.py` — data models (scripts depend on `DatasetOption` shape)
3. 6 scripts — implement and test individually with `uv run`
4. `SKILL.md` — references scripts by name
5. `data-collection.md` agent — references skill
