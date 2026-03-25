# DataAgent

A pipeline system for data exploration, analysis, and annotation. Each pipeline run is orchestrated by a primary agent that clarifies user intent, builds a JSON contract, and invokes specialized stage agents sequentially.

## Available Agents

| Agent | Mode | Purpose |
|---|---|---|
| `orchestrator` | primary | Main entry point — builds contract, runs pipeline stages |
| `data-collection` | subagent | Searches and downloads datasets from Kaggle, HuggingFace, and web |
| `data-quality` | subagent | Profiles data, detects issues, applies cleaning |
| `annotation` | subagent | Samples and annotates data, exports LabelStudio JSON with pre-annotations |

## Directory Conventions

- `.opencode/agents/` — Agent definitions (markdown with YAML frontmatter)
- `.opencode/skills/*/SKILL.md` — Skill definitions with instructions and scripts
- `workspace/` — Runtime artifacts (session directories, gitignored)
- `src/models.py` — DataContract Pydantic schema

## Session Workspace

Each pipeline run creates a timestamped session directory:

```
workspace/session-YYYY-MM-DDTHH:MM:SS/
├── contract.json
├── collection/
│   ├── data/
│   └── report.md
├── quality/
│   ├── data/
│   └── report.md
└── annotation/
    ├── labels.json
    └── report.md
```

## Contract Schema

The orchestrator writes a `contract.json` in the session directory:

```json
{
  "topic": "string — what the user wants data about",
  "domain": "string — field/industry",
  "timeframe": "string — how recent the data should be",
  "sources_preference": ["kaggle", "huggingface", "web"],
  "format_preference": "csv|json|parquet|any",
  "size_preference": "small|medium|large|any",
  "columns_of_interest": ["list of columns the user cares about"],
  "quality_requirements": "string — what quality means for this use case",
  "annotation_task": "classification|ner|regression|none",
  "annotation_labels": ["list of label categories if known"]
}
```

## Invoking Subagents

Use `@` mentions in prompts to invoke stage agents:

- `@data-collection` — Search and download datasets
- `@data-quality` — Profile and clean data
- `@annotation` — Sample data and produce LabelStudio-compatible labeled output

Pass the session directory path in the prompt so the subagent knows where to find the contract and write artifacts.
