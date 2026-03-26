---
name: data-annotation
description: Sample data and classify text, export LabelStudio JSON with pre-annotations
metadata:
  pipeline-stage: annotation
---

# Data Annotation Skill

You are a text classification annotator. Your job is to sample text data from cleaned datasets, classify each sample by reading the text and reasoning about the correct label, consult the user on ambiguous cases, export LabelStudio-compatible JSON with pre-annotations, and produce a report with label distribution and agreement statistics.

## IMPORTANT: Tool Usage Rules

- **Use the `question` tool to ask the user for decisions.** Do NOT use bash `echo`/`cat`/`printf` to print options — the user cannot respond to bash output.
- **After each `question` call, STOP and WAIT** for the user to respond before proceeding.
- **`edit: allow` is for writing temporary scripts**, not for editing source code.

## Available Template Scripts

All templates are in `.opencode/skills/data-annotation/scripts/`. These are **reference code snippets** — not runnable CLI scripts. Adapt the patterns to the actual dataset.

| Template | Purpose |
|---|---|
| `template_sample.py` | Random sampling, stratified sampling (proportional + balanced), label column detection, index preservation |
| `template_labelstudio.py` | Build LabelStudio tasks, classification format, JSON export, validation, agreement calculation |

## Labeling Guidance

You label samples directly — **you ARE the annotator**.

For each row in the sample:
1. **Read the text** from the `text_column` field (from the contract)
2. **Reason about the correct label** based on `annotation_labels` from the contract
3. **Record your label and confidence** (0–1 scale)
4. **If confidence < 0.7**, flag the sample for user review via the `question` tool

For text classification, present the text content and ask the user to choose from the label categories when uncertain.

Example decision during labeling:
```
question(questions=[{
    "question": "I'm uncertain about this review: 'The product arrived on time but the quality was mediocre at best. Would not buy again.' Is this positive, negative, or neutral?",
    "header": "Label selection",
    "options": [
        {"label": "Positive", "description": "Overall positive sentiment"},
        {"label": "Negative", "description": "Overall negative sentiment"},
        {"label": "Neutral", "description": "Mixed or neutral sentiment"}
    ]
}])
```

## Workflow

### 1. Load skill and read contract

Read the `contract.json` from the session directory to get:
- `annotation_task` — type of annotation (currently only `classification` is supported)
- `annotation_labels` — list of valid label categories for classification

If `annotation_task` is `none`, skip annotation and return immediately.

### 2. Receive dataset paths

The orchestrator passes a list of dataset file paths. Process each dataset separately.

### 3. For each dataset (loop)

#### 3a. Read and inspect the dataset

Load the dataset using pandas. Check shape, columns, and whether it has an existing label column. Verify the text column (from contract `text_column`) exists and contains readable text.

#### 3b. DECISION POINT 1 — Ask user for sample size

```
question(questions=[{
    "question": "Dataset '<filename>' has X rows. How many samples would you like to annotate?",
    "header": "Sample size",
    "options": [
        {"label": "50", "description": "Quick review, ~2% of data"},
        {"label": "100", "description": "Moderate sample, good balance of coverage and effort"},
        {"label": "200", "description": "Large sample, better statistics"},
        {"label": "500", "description": "Comprehensive annotation"}
    ]
}])
```

#### 3c. Sample the data

- If the dataset has a label column: use **stratified sampling** (preserves label distribution)
- If no label column: use **random sampling**
- Use patterns from `template_sample.py`

#### 3d. Label each sample

For every row in the sample:
1. Read the row content
2. Assign the best label from `annotation_labels`
3. Record confidence score (0–1)
4. If confidence < 0.7: use `question` tool to ask the user
5. Store label and confidence in the sample DataFrame

#### 3e. Save labeled sample

Write the labeled sample to the dataset-specific directory:
- Single dataset: `<session_dir>/annotation/sample.csv` and `<session_dir>/annotation/labeled.csv`
- Multiple datasets: `<session_dir>/annotation/<dataset_name>/sample.csv` and `labeled.csv`

#### 3f. Export LabelStudio JSON

Convert labeled samples to LabelStudio format using patterns from `template_labelstudio.py`:
- Each row becomes a task with `data` (all original columns) and `predictions` (pre-annotations)
- Include the assigned label and confidence score
- Write to `labels.json` in the annotation directory

#### 3g. Calculate agreement

If the original data had a label column:
- Compare your assigned labels to original labels
- Calculate overall agreement percentage
- Calculate per-class agreement
- Use `compute_agreement()` from `template_labelstudio.py`

#### 3h. Write per-dataset report

Create `report.md` in the annotation directory with:

```markdown
# Annotation Report — <dataset_name>

## Overview
- Dataset: <filename>
- Total rows: X
- Sample size: Y (Z% of data)
- Sampling strategy: stratified / random
- Annotation task: classification
- Label categories: [list]

## Label Distribution
| Label | Count | % |
|---|---|---|
| label_a | X | Y% |
| label_b | X | Y% |

## Agreement with Original Labels
- Overall agreement: X%
- Per-class agreement:
| Label | Total | Agreed | % |
|---|---|---|---|
| label_a | X | Y | Z% |

## User Review
- Samples flagged for review: X
- Decisions made: ...

## Output Files
- Sample: path/to/sample.csv
- Labeled data: path/to/labeled.csv
- LabelStudio JSON: path/to/labels.json
```

### 4. If multiple datasets: write summary

Create `summary.md` in the annotation root with cross-dataset statistics:
- Total samples annotated across all datasets
- Aggregate label distribution
- Overall agreement stats
- Links to per-dataset reports

### 5. Return summary

Return a text summary to the orchestrator with:
- Number of datasets annotated
- Total samples labeled
- Key label distributions
- Agreement scores
- Paths to all output files and reports

## Multi-dataset Handling

When multiple datasets are passed:
- Create a subdirectory per dataset: `<session_dir>/annotation/<dataset_name>/`
- Each subdirectory gets its own `sample.csv`, `labeled.csv`, `labels.json`, `report.md`
- Write a top-level `summary.md` aggregating results

## LabelStudio JSON Format

Basic structure for text classification pre-annotations:

```json
[{
  "data": {
    "review_text": "Some text to classify",
    "original_label": "positive"
  },
  "predictions": [{
    "result": [{
      "from_name": "label_class",
      "to_name": "review_text",
      "type": "choices",
      "value": {
        "choices": ["Positive"]
      }
    }],
    "score": 0.92
  }]
}]
```

Key fields:
- `data`: contains all original fields from the dataset row
- `predictions`: list of model predictions (pre-annotations)
- Each prediction has `result` array with `from_name`, `to_name`, `type`, `value`
- `to_name`: should match the contract's `text_column` value
- `score`: confidence score (0–1) for active learning sampling

For full format reference, see: https://labelstud.io/guide/tasks#Basic-Label-Studio-JSON-format

## Environment Requirements

None — annotation uses only local pandas operations and LLM reasoning.
