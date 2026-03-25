# TODO: Data Annotation Agent

## Overview

Implement the third pipeline stage — data annotation. The agent receives a list of dataset paths from the orchestrator, processes each dataset separately, samples data (preserving label distribution if labels exist), labels samples directly as an LLM annotator, asks the user for ambiguous cases via `question` tool, exports LabelStudio-compatible JSON with pre-annotations, and produces a report with label distribution and % agreement with initial labels.

## Workspace structure

**Single dataset:**
```
workspace/session-.../annotation/
├── sample.csv
├── labeled.csv
├── labels.json
└── report.md
```

**Multiple datasets:**
```
workspace/session-.../annotation/
├── dataset_1/
│   ├── sample.csv
│   ├── labeled.csv
│   ├── labels.json
│   └── report.md
├── dataset_2/
│   ├── sample.csv
│   ├── labeled.csv
│   ├── labels.json
│   └── report.md
└── summary.md
```

## Files to create (4 total)

### 1. `.opencode/agents/annotation.md`

Frontmatter:
```yaml
description: Samples and annotates data, exports LabelStudio JSON with pre-annotations
mode: subagent
temperature: 0.1
steps: 40
permission:
  bash:
    "*": allow
  edit: allow
```

Workflow:
1. Load skill, read contract for `annotation_task` and `annotation_labels`
2. **Receive list of dataset paths** from orchestrator prompt
3. **For each dataset** (loop):
   a. Read dataset, check if it has existing label column
   b. Ask user for sample size for THIS dataset
   c. Stratified sample if labels exist, random if not
   d. **Label each sample directly** — read the row data, reason about the correct label based on `annotation_labels` from the contract. If uncertain about a sample, use `question` tool to ask the user.
   e. Store labeled samples in original format (CSV/JSON) in dataset-specific dir
   f. Convert to LabelStudio JSON with pre-annotations
   g. Calculate % agreement with initial labels (if present)
   h. Write per-dataset report.md
4. If multiple datasets: write `summary.md` with cross-dataset stats
5. Return summary

### 2. `.opencode/skills/data-annotation/SKILL.md`

Frontmatter:
```yaml
name: data-annotation
description: Sample data and annotate it, export LabelStudio JSON with pre-annotations
metadata:
  pipeline-stage: annotation
```

Contents:
- Available templates with descriptions
- **Labeling guidance**:
  - You label samples directly — you ARE the annotator
  - For each row: read the row data, reason about which label from `annotation_labels` fits best
  - Record your label and confidence (0-1)
  - If confidence < 0.7, flag for user review via `question` tool
  - For classification tasks, present the row content and ask the user to choose from the label categories when uncertain
- Workflow with DECISION POINTS:
  - **Per dataset**: ask user for sample size
  - **During labeling**: ask user for ambiguous cases via `question` tool
- Multi-dataset handling: iterate, create subdirs if >1 dataset
- LabelStudio JSON format reference:

**Basic Label Studio JSON format for pre-annotations:**
```json
[{
  "data": {
    "my_text": "Some text to classify",
    "original_label": "positive"
  },
  "predictions": [{
    "result": [{
      "from_name": "sentiment_class",
      "to_name": "my_text",
      "type": "choices",
      "value": {
        "choices": ["Positive"]
      }
    }],
    "score": 0.92
  }]
}]
```

For full format reference, see: https://labelstud.io/guide/tasks#Basic-Label-Studio-JSON-format

Key fields:
- `data`: contains all original fields from the dataset row
- `predictions`: list of model predictions (pre-annotations)
- Each prediction has `result` array with `from_name`, `to_name`, `type`, `value`
- `score`: confidence score (0-1) for active learning sampling

- Report.md template:
  - Sample size and sampling strategy
  - Label distribution (bar chart or table)
  - % agreement with initial labels (if present)
  - Per-class agreement
  - Number of samples flagged for user review
  - Decisions made and reasoning

### 3. Templates (2 files in `.opencode/skills/data-annotation/scripts/`)

#### `template_sample.py` — Sampling patterns

Demonstrates:
- Random sampling: `df.sample(n=N, random_state=42)`
- Stratified sampling: `df.groupby(label_col).apply(lambda g: g.sample(n=..., random_state=42))`
- Calculating per-stratum sample sizes proportional to group size
- Handling datasets without label columns (fall back to random)
- Preserving original indices for traceability
- Saving sample with original index column

#### `template_labelstudio.py` — LabelStudio JSON export

Demonstrates:
- Building task list: one dict per row
- `data` key: mapping all original columns
- `predictions` key: array with single result
- Classification format: `type: "choices"`, `from_name`, `to_name`, `value.choices`
- Including confidence as `score`
- Writing JSON list to file

### 4. `tests/test_data_annotation.py`

Tests:
- Template scripts have valid Python syntax (compile check)
- SKILL.md has valid frontmatter with correct `name`
- Agent definition has valid frontmatter
- Example LabelStudio JSON structure validation

## Agreement calculation

If original data has a label column:
```
agreement_pct = (matching_labels / total_labeled) * 100
```
Report per-class and overall agreement in report.md.

## Execution order

1. 2 template scripts — create all at once
2. `SKILL.md` — references templates, defines workflow and decision points
3. `annotation.md` agent — references skill
4. Tests — verify syntax and structure
5. Update orchestrator agent — pass dataset paths list
