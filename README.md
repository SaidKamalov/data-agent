# DataAgent

An agent-based pipeline for text classification — from data collection through quality analysis, annotation, and active learning simulation. Built on the [opencode](https://opencode.ai) agent framework.

Point opencode at your text classification task, and the pipeline finds datasets, cleans data, labels samples with LLM reasoning, and runs active learning to improve your classifier with fewer labeled examples.

## Quick Start

```bash
# 1. Clone and set up
git clone <repo-url> && cd DataAgent

# 2. Configure credentials
cp .env_example .env
# Edit .env with your API keys:
#   KAGGLE_USERNAME=your_username
#   KAGGLE_API_TOKEN=your_token
#   HUGGINGFACE_TOKEN=hf_your_token

# 3. Install dependencies
uv sync

# 4. Run opencode with the orchestrator
# opencode will auto-discover AGENTS.md and start the pipeline
```

Then describe your text classification task in natural language:

> "I need data to classify product reviews as positive, negative, or neutral"

The orchestrator will ask clarifying questions, build a contract, and run the full pipeline.

## Pipeline

Every run executes 4 mandatory stages:

```
collection  →  quality  →  annotation  →  active-learning
 [Kaggle]      [profile]    [LLM labels]    [TF-IDF + LogReg]
 [HuggingFace] [clean]      [LabelStudio]   [uncertainty sampling]
 [web]         [text QC]    [agreement]     [learning curve]
```

Each stage is handled by a dedicated subagent with specialized skills and helper scripts. Human-in-the-loop decisions happen via the `question` tool — the pipeline pauses at key points and asks for your input.

## Agents & Skills

### Agents

| Agent | Mode | Purpose |
|---|---|---|
| `orchestrator` | primary | Clarifies intent, builds contract, delegates to subagents |
| `data-collection` | subagent | Searches Kaggle/HuggingFace/web, presents options, downloads |
| `data-quality` | subagent | Profiles text quality, detects issues, applies cleaning |
| `annotation` | subagent | Samples data, classifies text, exports LabelStudio JSON |
| `active-learning` | subagent | Trains TF-IDF + LogReg, runs AL simulation, compares baseline |

### How it works

- **Agent definitions** live in `.opencode/agents/` as markdown files with YAML frontmatter (mode, permissions, temperature)
- **Skills** live in `.opencode/skills/*/SKILL.md` — detailed workflow instructions that agents load and follow
- **Scripts** in `.opencode/skills/*/scripts/` come in two types:
  - **CLI scripts** (e.g., `search_kaggle.py`) — runnable via `uv run`, accept `--args`, output JSON to stdout
  - **Templates** (e.g., `template_train_classifier.py`) — reference code snippets the agent adapts to its specific task
- **Orchestration**: The orchestrator uses `task()` to spawn subagents. Subagents self-execute by loading their skill and running scripts. The orchestrator NEVER uses `skill()` or does stage work directly.
- **Human-in-the-loop**: Subagents use the `question` tool at decision points. The tool pauses execution and waits for user input. Bash does NOT pause.

## Project Structure

```
DataAgent/
├── AGENTS.md                           # opencode project rules (auto-discovered)
├── PROJECT_SPEC.md                     # Full specification and data contract schema
├── opencode.json                       # opencode config (default_agent: orchestrator)
├── pyproject.toml                      # Python project config + dependencies
├── .env_example                        # Template for API credentials
├── src/
│   └── models.py                       # DataContract Pydantic schema
├── .opencode/
│   ├── agents/                         # Agent definitions (markdown + YAML)
│   │   ├── orchestrator.md
│   │   ├── data-collection.md
│   │   ├── data-quality.md
│   │   ├── annotation.md
│   │   └── active-learning.md
│   └── skills/                         # Skill definitions + scripts
│       ├── data-collection/
│       │   ├── SKILL.md                # Collection workflow
│       │   └── scripts/
│       │       ├── search_kaggle.py    # CLI: Kaggle API search
│       │       ├── download_kaggle.py  # CLI: Kaggle download
│       │       ├── search_huggingface.py
│       │       ├── download_huggingface.py
│       │       ├── template_scrape_web.py    # Template: web scraping
│       │       └── template_call_api.py      # Template: REST API
│       ├── data-quality/
│       │   ├── SKILL.md                # Quality workflow
│       │   └── scripts/
│       │       ├── template_read_data.py
│       │       ├── template_missing_values.py
│       │       ├── template_duplicates.py
│       │       ├── template_outliers_iqr.py
│       │       ├── template_impute_missing.py
│       │       └── template_text_quality.py  # Text-specific QC
│       ├── data-annotation/
│       │   ├── SKILL.md                # Annotation workflow
│       │   └── scripts/
│       │       ├── template_sample.py
│       │       └── template_labelstudio.py
│       └── active-learning/
│           ├── SKILL.md                # Active learning workflow
│           └── scripts/
│               ├── template_train_classifier.py
│               ├── template_uncertainty.py
│               └── template_visualize.py
├── tests/                              # Integration tests
│   ├── test_data_collection.py
│   ├── test_data_quality.py
│   └── test_data_annotation.py
├── TODOs/                              # Implementation plans for each stage
│   ├── todo_orchestrator.md
│   ├── todo_data_collection.md
│   ├── todo_data_quality.md
│   ├── todo_annotation.md
│   ├── todo_active_learning.md
│   └── todo_text_classification_focus.md
└── workspace/                          # Runtime artifacts (gitignored)
```

## Session Workspace

Each pipeline run creates a timestamped session directory under `workspace/`:

```
workspace/session-2026-03-25T14:30:00/
├── contract.json                  # Data contract (user requirements formalized)
├── collection/
│   ├── data/                      # Downloaded dataset files
│   └── report.md                  # Sources searched, selection rationale
├── quality/
│   ├── data/                      # Cleaned dataset
│   └── report.md                  # Profile, issues found, cleaning decisions
├── annotation/
│   ├── sample.csv                 # Sampled rows
│   ├── labeled.csv                # Sample + assigned labels + confidence
│   ├── labels.json                # LabelStudio-compatible pre-annotations
│   └── report.md                  # Label distribution, agreement stats
└── active-learning/
    ├── selected_samples.csv       # Samples selected per AL iteration
    ├── learning_curve.csv         # Performance metrics per iteration
    ├── model_metrics.json         # Baseline vs AL comparison
    ├── learning_curve.png         # Visualization
    └── report.md                  # Full AL report
```

## Data Contract

The orchestrator formalizes user requests into a JSON contract that all subagents read:

```json
{
  "topic": "product review sentiment analysis",
  "domain": "e-commerce",
  "timeframe": "2024-2025",
  "sources_preference": ["kaggle", "huggingface", "web"],
  "format_preference": "csv",
  "size_preference": "medium",
  "text_column": "review_text",
  "columns_of_interest": ["rating", "product_category"],
  "quality_requirements": "English only, no empty texts",
  "annotation_task": "classification",
  "annotation_labels": ["positive", "negative", "neutral"],
  "al_strategy": "entropy",
  "al_val_split": 0.2
}
```

## Scripts Convention

**CLI scripts** (runnable):
- Accept arguments via `argparse`
- Output JSON to stdout (logs to stderr)
- Use `uv run .opencode/skills/<skill>/scripts/<script>.py --arg value`
- Exit 0 on success, non-zero on failure
- Load credentials from `.env` via `python-dotenv`

**Templates** (reference code):
- Pure Python functions with type hints and docstrings
- Not runnable directly — agents adapt patterns to their specific task
- Prefixed with `template_`

## Dependencies

| Category | Packages |
|---|---|
| Data | pandas, numpy, scipy |
| ML | scikit-learn, matplotlib |
| APIs | kaggle, huggingface_hub, requests, requests-html |
| Annotation | label-studio |
| Config | python-dotenv, pyyaml, pydantic |
| Dev | pytest, ruff |

## Development

```bash
# Install dependencies
uv sync

# Lint
uv run ruff check

# Run tests
uv run pytest tests/ -v

# Run a specific script
uv run .opencode/skills/data-collection/scripts/search_kaggle.py --query "sentiment analysis" --max-results 5
```
