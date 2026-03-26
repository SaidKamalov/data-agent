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

Subagents are invoked via the `task()` tool, NOT the `skill()` tool. The `skill()` tool loads instructions into the current agent's context (self-execution). The `task()` tool spawns an independent agent session.

Each pipeline stage must be delegated to its corresponding subagent:

### data-collection

```
task(
  description="Search and download datasets",
  prompt="Session directory: workspace/session-YYYY-MM-DDTHH:MM:SS/. Read contract.json from there. Search for datasets matching the contract requirements using the available search scripts. Present options to the user, download the selected dataset, and write a collection report.",
  subagent_type="data-collection"
)
```

### data-quality

```
task(
  description="Profile and clean collected data",
  prompt="Session directory: workspace/session-YYYY-MM-DDTHH:MM:SS/. Read contract.json and profile the data in collection/data/. Detect quality issues, consult the user on cleaning strategies, apply cleaning, and write a quality report.",
  subagent_type="data-quality"
)
```

After this stage completes, the orchestrator must list files in `quality/data/` to discover the cleaned dataset paths before invoking annotation.

### annotation (only if annotation_task ≠ "none")

```
task(
  description="Sample and annotate data",
  prompt="Session directory: workspace/session-YYYY-MM-DDTHH:MM:SS/. Read contract.json for annotation_task and annotation_labels. Cleaned data files to annotate: workspace/session-.../quality/data/cleaned.csv. For each file: sample, label, export LabelStudio JSON, write report.",
  subagent_type="annotation"
)
```

**The orchestrator must NEVER load skills or execute stage work directly.** Its only jobs are:
1. Clarify user intent
2. Create session workspace
3. Write contract.json
4. Discover cleaned data files after quality stage (via `ls`)
5. Delegate each stage to its subagent via `task()`, passing explicit file paths
6. Verify each stage produced expected output before proceeding
7. Present final results
