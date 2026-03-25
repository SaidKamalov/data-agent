# TODO: Orchestrator Agent

## Overview

Create the main orchestrator — a primary agent that takes user requests, clarifies intent, builds a JSON contract, creates a session workspace, and sequentially invokes stage agents. This is the entry point for the entire DataAgent pipeline.

## Files to create (2 total)

### 1. `.opencode/agents/orchestrator.md`

Frontmatter:
```yaml
description: Main orchestrator for the data pipeline — clarifies user intent, builds contract, runs stage agents
mode: primary
temperature: 0.1
permission:
  bash:
    "*": allow
  edit: allow
```

Workflow the agent follows:
1. **Understand request** — Parse the user's initial message
2. **Ask 2-4 clarifying questions** using the `question` tool:
   - Domain/field of interest
   - Timeframe (how recent the data should be)
   - Format preference (CSV, JSON, Parquet, any)
   - Size preference (small/medium/large)
   - What columns/attributes they care about
   - Annotation needs (classification, NER, none)
3. **Create session workspace** — Create the directory structure for this pipeline session:
   ```bash
   SESSION_DIR="workspace/session-$(date -u +%Y-%m-%dT%H:%M:%S)"
   mkdir -p "$SESSION_DIR/collection/data" "$SESSION_DIR/quality/data"
   ```
   Only `collection/data/` and `quality/data/` directories are needed at start. Other files (`contract.json`, `report.md`) are written by agents as they run.
4. **Write contract.json** — Formalize answers into the `DataContract` JSON schema:
   ```json
   {
     "topic": "...",
     "domain": "...",
     "timeframe": "...",
     "sources_preference": ["kaggle", "huggingface", "web"],
     "format_preference": "csv|json|parquet|any",
     "size_preference": "small|medium|large|any",
     "columns_of_interest": ["..."],
     "quality_requirements": "...",
     "annotation_task": "none",
     "annotation_labels": []
   }
   ```
5. **Invoke @data-collection** — Pass the session directory path in the prompt. Wait for result.
6. **Invoke @data-quality** — Pass session dir + path to collected data. Wait for result.
7. **Invoke @annotation** — IF `annotation_task` in contract is not "none":
   Pass session dir + list of dataset paths from `collection/data/`. Wait for result.
8. **Present results** — Summarize what was done, list all artifact paths

Key design decisions:
- **All 3 stages**: collection → quality → annotation (annotation only runs if `annotation_task` != 'none')
- **@ mention** to invoke subagents — opencode resolves them by matching agent descriptions
- **Session dir path passed in prompt** — subagents read `contract.json` and know where to write artifacts
- **`edit: allow`** — needs to write `contract.json` and create directories
- **No `permission.task` restriction** — allows invoking any subagent
- **Include DataContract schema in the agent body** so the agent knows the exact JSON structure

### 2. `AGENTS.md` — Project context for LLM agents

Auto-discovered by opencode from project root. This file is read by the LLM, so it should contain only what the agent needs to know — not developer rules.

Contents:
- **Project description** — What DataAgent is (pipeline system for data exploration)
- **Available agents** — Table of agents and their roles:
  | Agent | Mode | Purpose |
  |---|---|---|
  | `orchestrator` | primary | Main entry point, builds contract, runs pipeline |
  | `data-collection` | subagent | Searches and downloads datasets |
  | `data-quality` | subagent | Profiles and cleans data |
  | `annotation` | subagent | Samples and annotates data, exports LabelStudio JSON |
- **Directory conventions**:
  - `.opencode/agents/` — agent definitions
  - `.opencode/skills/*/SKILL.md` — skill definitions
  - `workspace/` — runtime artifacts (gitignored)
  - `src/models.py` — DataContract Pydantic schema
- **Session workspace format** — `session-YYYY-MM-DDTHH:MM:SS`
- **Contract schema** — Include the JSON structure so the orchestrator knows exactly what to write
- **How to invoke subagents** — Use @ mention (e.g., `@data-collection`)

What NOT to include: development rules (uv, ruff, type hints, testing). Those belong in PROJECT_SPEC.md for developers, not in AGENTS.md for the LLM.

## Execution order

1. `AGENTS.md` — project rules (opencode reads this first)
2. `orchestrator.md` — primary agent (references contract schema and subagents)

## Testing

The orchestrator is an LLM agent — cannot be unit tested. Verify by:
1. Starting opencode with the orchestrator agent selected
2. Sending a request like "I need data about climate change"
3. Confirming the agent asks clarifying questions
4. Confirming it creates a session workspace and contract.json
5. Confirming it invokes @data-collection and @data-quality in sequence
6. Confirming it invokes @annotation after quality (if annotation requested)
