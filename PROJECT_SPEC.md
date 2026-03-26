# DataAgent — Project Specification

## Overview

An agent system for text data collection, quality analysis, and classification annotation, built on top of the opencode agent framework. The system implements a 3-stage pipeline focused on text classification tasks (narrative classification, topic classification, sentiment analysis, and similar). Each stage is handled by a dedicated subagent with specialized skills and helper scripts. Human-in-the-loop is achieved via the `question` tool within skill definitions.

## Pipeline Stages

1. **Data Collection** — Search and download text classification datasets from Kaggle, HuggingFace, and web sources
2. **Data Quality** — Profile text-related quality issues (encoding, empty texts, class imbalance, text length), apply fixes
3. **Annotation** — Sample text data and classify it with LabelStudio-compatible labeled output
4. _(Reserved for future stage)_
5. _(Reserved for future stage — outside current text classification scope)_

## Architecture

### Agents (4 defined + 1 placeholder)

| Agent | Mode | Purpose |
|---|---|---|
| `orchestrator` | primary | Takes user request, asks clarifying questions, builds JSON contract, sequentially invokes stage agents |
| `data-collection` | subagent | Searches configured sources for text classification datasets, presents options, downloads dataset |
| `data-quality` | subagent | Profiles text data quality, detects issues, applies user-approved cleaning |
| `annotation` | subagent | Samples text data, applies classification labels, exports LabelStudio JSON |

### Communication

- **Orchestrator → Subagents**: Passes JSON contract (and artifact paths for later stages)
- **Subagents → Orchestrator**: File-based artifacts (datasets, reports) + text summary returned from Task
- **HITL**: In-skill `question` tool calls at decision points (Option B from original discussion)
- **Configuration**: All agent config (mode, permissions, model, temperature) lives in markdown frontmatter in `.opencode/agents/`. `AGENTS.md` is auto-discovered from project root. No `opencode.json` needed.

### Data Contract Schema

The orchestrator formalizes user requests into this JSON object:

```json
{
  "topic": "string — what the user wants data about",
  "domain": "string — field/industry",
  "timeframe": "string — how recent the data should be",
  "sources_preference": ["kaggle", "huggingface", "web"],
  "format_preference": "csv|json|parquet|any",
  "size_preference": "small|medium|large|any",
  "text_column": "string — name of the text column to classify",
  "columns_of_interest": ["list of other columns the user cares about"],
  "quality_requirements": "string — what quality means for this use case",
  "annotation_task": "classification",
  "annotation_labels": ["list of label categories if known"]
}
```

## Directory Structure

```
DataAgent/
├── PROJECT_SPEC.md                     # This file
├── AGENTS.md                           # opencode project rules (auto-discovered)
├── .env_example                        # Template for required env variables
├── .env                                # Actual credentials (gitignored)
├── pyproject.toml                      # Python project config + dependencies
├── main.py                             # CLI entry point (future)
├── .opencode/
│   ├── agents/
│   │   ├── orchestrator.md             # Primary orchestrator agent
│   │   ├── data-collection.md          # Stage 1 subagent
│   │   ├── data-quality.md             # Stage 2 subagent
│   │   └── annotation.md              # Stage 3 subagent
│   └── skills/
│       ├── data-collection/
│       │   ├── SKILL.md                # Instructions for data collection stage
│       │   └── scripts/
│       │       ├── search_kaggle.py    # Kaggle API dataset search
│       │       ├── search_huggingface.py  # HuggingFace Hub search
│       │       ├── scrape_web.py       # requests-html web scraping
│       │       └── download_dataset.py # Unified dataset downloader
│       ├── data-quality/
│       │   ├── SKILL.md                # Instructions for data quality stage
│       │   └── scripts/
│       │       ├── profile_data.py     # Shape, dtypes, missing, distributions
│       │       ├── detect_outliers.py  # IQR / z-score outlier detection
│       │       ├── detect_duplicates.py # Exact + fuzzy dedup
│       │       └── clean_data.py       # Apply cleaning transformations
│       └── data-annotation/
│           ├── SKILL.md                # Instructions for annotation stage
│           └── scripts/
│               ├── sample_data.py      # Stratified / random sampling
│               ├── generate_labels.py  # Rule-based or LLM-assisted labeling
│               └── export_labelstudio.py # Convert labels → LabelStudio JSON
├── src/
│   └── models.py                       # Pydantic data contract model
├── workspace/                          # Runtime artifacts (gitignored)
│   └── session-<ISO-8601-timestamp>/   # One subfolder per orchestrator session
│       ├── contract.json
│       ├── collection/
│       │   ├── data/
│       │   └── report.md
│       ├── quality/
│       │   ├── data/
│       │   └── report.md
│       └── annotation/
│           ├── labels.json
│           └── report.md
└── tests/
```

## Session Workspace Convention

The orchestrator creates a new session subfolder under `workspace/` each time it starts a pipeline:

```
workspace/session-2026-03-24T23:00:00/
```

Format: `session-YYYY-MM-DDTHH:MM:SS` (ISO 8601 without timezone offset for filesystem safety).

Each stage agent writes its artifacts into the corresponding subfolder (`collection/`, `quality/`, `annotation/`). This keeps multiple pipeline runs isolated and traceable.

## Script Convention

All helper scripts in `skills/*/scripts/` follow this pattern:
- Accept CLI arguments via `argparse`
- Print results to stdout as JSON (for machine consumption)
- Accept `--input` for data paths, `--output` for output paths
- Exit code 0 on success, non-zero on failure
- No interactive prompts (all config via CLI args)

## Python Dependencies

```toml
dependencies = [
    "pandas",
    "numpy",
    "kaggle",
    "huggingface_hub",
    "requests-html",
    "scipy",
    "scikit-learn",
    "python-dotenv",
]
```

## End-to-End Flow

```
User: "I need data for classifying product reviews as positive, negative, or neutral"

Orchestrator:
  → Creates workspace/session-2026-03-25T10:00:00/
  → "What text column should contain the review text? (e.g., 'review_text')"
  → "What format do you prefer? CSV, JSON, or any?"
  → "How large a dataset? Small (<1k rows), medium, or large?"
  → Writes contract.json with text_column="review_text", annotation_labels=["positive", "negative", "neutral"]

  → Invokes @data-collection:
    → Searches Kaggle: finds "Amazon Product Reviews" and "Yelp Reviews Dataset"
    → Searches HuggingFace: finds "imdb-reviews" and "amazon_polarity"
    → Websearch: finds a public review API
    → "Which dataset?" → User picks Kaggle "Amazon Product Reviews"
    → Downloads, writes report.md, returns summary

  → Invokes @data-quality:
    → Checks text column: 2% empty texts, 5% under 5 words
    → Class distribution: 55% positive, 30% negative, 15% neutral (imbalanced)
    → Encoding: 0.1% rows with mojibake characters
    → "Filter rows with empty text?" → Yes
    → "Address class imbalance?" → Keep as-is, use stratified sampling
    → Cleans, writes report.md, returns summary

  → Invokes @annotation:
    → "How many samples to label? Sampling strategy?"
    → "Label categories: [positive, negative, neutral]?"
    → Samples 200 rows, classifies each review by reading the text
    → Exports LabelStudio JSON, writes report.md, returns summary

  → Presents to user:
    "Pipeline complete. Artifacts:
     - Dataset: workspace/session-.../collection/data/amazon_reviews.csv
     - Quality report: workspace/session-.../quality/report.md
     - Cleaned data: workspace/session-.../quality/data/cleaned.csv
     - Labels: workspace/session-.../annotation/labels.json
     - Annotation report: workspace/session-.../annotation/report.md"
```

## Development Rules

- **Package manager**: Use `uv` for all dependency management and script execution (`uv run`, `uv add`, etc.)
- **Linting**: Run `uv run ruff check` before committing. Follow ruff defaults.
- **Type hints**: Add type hints to all function signatures.
- **Docstrings**: Add concise but clear docstrings to every function and module.
- **Opencode reference**: Always check opencode docs when defining agents or skills — verify frontmatter fields, valid locations, and naming rules.
- **Script independence**: Each helper script must be runnable standalone via CLI args. Test individually before integrating into a skill.
- **No hardcoded paths**: All paths come from CLI args or environment. Use `pathlib.Path` for path manipulation.
- **Error handling**: Scripts should catch exceptions, print a clear error message to stderr, and exit with non-zero code.
- **Output format**: Scripts output JSON to stdout. Never mix log messages with JSON output (use stderr for logs).
- **Credentials**: Never hardcode API keys, tokens, or secrets in scripts. Load them from `.env` using `python-dotenv` or `os.environ`. The `.env` file is gitignored. Always provide a `.env_example` file at the project root listing all required variables with placeholder values so new users can copy it (`cp .env_example .env`) and fill in their own credentials.
- **Environment variables in scripts**: Use `load_dotenv()` at the top of scripts (after `argparse`) and access values via `os.getenv("VAR_NAME")`. Fail early with a clear message if a required variable is missing.
- **Testing helper scripts**: Write integration tests for every helper script in `tests/test_<stage>.py`. Run scripts via subprocess (`sys.executable`), validate JSON output structure, and confirm files are created where expected. Use `pytest.mark.skipif` for tests that require external credentials. Store test artifacts in a temporary `test_<stage>-session/` directory under `tests/` and clean up automatically with a session-scoped autouse fixture. See `tests/test_data_collection.py` as the reference implementation.
- **LabelStudio format**: When producing annotation exports, follow the JSON format at https://labelstud.io/guide/tasks#Basic-Label-Studio-JSON-format
