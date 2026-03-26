# TODO: Active Learning Agent

## Overview

Add a 4th pipeline stage that implements active learning simulation. The agent trains a TF-IDF + Logistic Regression classifier on labeled samples, iteratively selects the most uncertain unlabeled texts, simulates labeling via ground truth, retrains, and tracks performance. Both annotation and active-learning stages are **mandatory** — the pipeline is always: collection → quality → annotation → active-learning → present results.

## Key Design Decisions

| Decision | Choice |
|---|---|
| Unlabeled pool source | Remaining rows from cleaned dataset (not sampled by annotation) |
| Golden set | If original label exists: rows where assigned_label == original_label. Else: all labeled rows |
| Loop mode | Automated simulation (labels read from ground truth in cleaned dataset) |
| Model | TF-IDF + Logistic Regression only (no transformers) |
| Output scope | Selected samples + learning curve + baseline comparison (no saved model) |
| HITL points | Ask user for batch size and number of iterations before loop starts |
| Mandatory | Both annotation and AL always run — no conditional skips |

## Files to create/modify (10 total)

### 1. `src/models.py` — Add 2 AL fields to DataContract

Add these fields (backward-compatible defaults):

```python
al_strategy: str = "entropy"     # entropy | margin | random
al_val_split: float = 0.2
```

Do NOT add `active_learning_enabled` — AL is always mandatory.

Updated contract schema:

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
  "annotation_labels": ["list of label categories if known"],
  "al_strategy": "entropy",
  "al_val_split": 0.2
}
```

### 2. `pyproject.toml` — Add matplotlib dependency

Run: `uv add matplotlib`

Required for `template_visualize.py` learning curve plots.

### 3. `PROJECT_SPEC.md` — Add stage 4 + contract fields

| Section | Change |
|---|---|
| Pipeline stages | Replace "Reserved for future stage" with: **Active Learning** — Train TF-IDF + LogReg on labeled samples, iteratively select uncertain unlabeled texts, simulate labeling, track performance, compare baseline vs AL |
| Agent table | Add row for `active-learning` subagent |
| Contract schema | Add `al_strategy` and `al_val_split` fields |
| End-to-end flow | Add a second flow example showing the full pipeline including AL stage |

### 4. `AGENTS.md` — Add agent row + invocation example

| Section | Change |
|---|---|
| Agent purpose table | Add: `active-learning` \| subagent \| Trains TF-IDF + LogReg on labeled samples, iteratively selects uncertain texts for annotation |
| Contract schema | Add `al_strategy` and `al_val_split` |
| Invocation examples | Add new block for active-learning delegation |

Invocation example:

```
### active-learning

task(
  description="Active learning simulation for: <contract.topic>",
  prompt="Session directory: workspace/session-YYYY-MM-DDTHH:MM:SS/. Read contract.json for al_strategy and al_val_split. Labeled data: workspace/session-.../annotation/labeled.csv. Full dataset: workspace/session-.../quality/data/cleaned.csv. Run active learning simulation, output to workspace/session-.../active-learning/.",
  subagent_type="active-learning"
)
```

### 5. `.opencode/agents/orchestrator.md` — Remove conditional, add AL step

| Area | Change |
|---|---|
| Step 7 (annotation) | Remove the `if annotation_task == 'none'` conditional. Annotation is always mandatory. |
| New step 8 (active-learning) | Add delegation to active-learning subagent. Discover `labeled.csv` from annotation and `cleaned.csv` from quality. Pass explicit paths. |
| Step 9 (present results) | Renumber from 8. Add AL artifacts to final summary: selected_samples.csv, learning_curve.csv, learning_curve.png, model_metrics.json, report.md |

Step 8 template:

```
### 8. Delegate to active-learning subagent

Discover the annotation output and cleaned data:
```bash
ls "<SESSION_DIR>/annotation/labeled.csv"
ls "<SESSION_DIR>/quality/data/" | grep -E '\.csv$'
```

Launch the active-learning subagent:
```
task(
  description="Active learning simulation for: <contract.topic>",
  prompt="You are the active-learning agent. Session directory: <SESSION_DIR>. Read contract.json for text_column, annotation_labels, al_strategy, al_val_split. Input files: labeled.csv from annotation (<SESSION_DIR>/annotation/labeled.csv), cleaned.csv from quality (<SESSION_DIR>/quality/data/cleaned.csv). Run active learning simulation. Output to <SESSION_DIR>/active-learning/.",
  subagent_type="active-learning"
)
```

Wait for completion, then verify:
```bash
ls "<SESSION_DIR>/active-learning/"
```
```

### 6. `.opencode/agents/active-learning.md` — Agent definition (CREATE)

Frontmatter:
```yaml
---
description: Trains TF-IDF + LogReg on labeled samples, iteratively selects uncertain texts for annotation
mode: subagent
temperature: 0.1
steps: 50
permission:
  bash:
    "*": allow
  edit: allow
---
```

Body sections:
- **CRITICAL RULES** (same pattern: never use bash echo/cat/printf, use question tool, stop-and-wait, one question per decision)
- **Instructions**:
  1. Load skill from `.opencode/skills/active-learning/SKILL.md`
  2. Read contract: `text_column`, `annotation_labels`, `al_strategy`, `al_val_split`
  3. Load input files: `labeled.csv` (annotation output), `cleaned.csv` (quality output)
  4. Build golden set (agreement rows if original label exists, else all labeled)
  5. Build unlabeled pool (cleaned.csv minus golden set's original_index)
  6. Split golden set into train/val by `al_val_split`
  7. Train baseline TF-IDF + LogReg, evaluate → BASELINE METRICS
  8. **HITL**: Ask user for batch size and number of iterations
  9. Run active learning loop (see skill workflow)
  10. Compare baseline vs final AL model
  11. Generate learning curve plot
  12. Write outputs: selected_samples.csv, learning_curve.csv, model_metrics.json, learning_curve.png, report.md
  13. Return summary with comparison
- **Output structure** (directory tree)
- **Note**: `edit: allow` for writing temp scripts

### 7. `.opencode/skills/active-learning/SKILL.md` — Skill definition (CREATE)

Frontmatter:
```yaml
---
name: active-learning
description: Train TF-IDF + LogReg and run active learning simulation loop
metadata:
  pipeline-stage: active-learning
---
```

Body sections:
- Role description
- **IMPORTANT: Tool Usage Rules** (question tool, stop-and-wait, edit:allow justification)
- **Available Template Scripts** table:

| Template | Purpose |
|---|---|
| `template_train_classifier.py` | Build TF-IDF + LogReg pipeline, train, evaluate, predict probabilities |
| `template_uncertainty.py` | Entropy, margin, least-confidence scores; top-k selection |
| `template_visualize.py` | Matplotlib learning curve and baseline comparison plots |

- **Workflow** (detailed numbered steps):
  1. Load data and build golden set
  2. Build unlabeled pool
  3. Split into train/validation
  4. Train baseline model, evaluate → record iteration 0
  5. **DECISION POINT 1**: Ask user for batch size and iterations
  6. AL loop (N iterations):
     a. Predict on unlabeled pool → probabilities
     b. Compute uncertainty scores (strategy from contract)
     c. Select top-k uncertain samples
     d. Simulate labels (read ground truth from cleaned.csv)
     e. Move selected samples to labeled set
     f. Retrain on expanded labeled set
     g. Evaluate on validation → record metrics
  7. Compare baseline (frozen) vs final AL model
  8. Generate learning curve plot
  9. Write outputs
  10. Return summary

- **DECISION POINT example**:
```
question(questions=[{
    "question": "How many samples should I select per iteration, and how many iterations?",
    "header": "AL configuration",
    "options": [
        {"label": "50 samples, 5 iterations", "description": "Standard batch size, moderate exploration"},
        {"label": "100 samples, 3 iterations", "description": "Larger batches, fewer rounds"},
        {"label": "25 samples, 10 iterations", "description": "Smaller batches, more fine-grained selection"},
        {"label": "Custom", "description": "Specify your own values"}
    ]
}])
```

- **Uncertainty formulas reference**:
  - Entropy: H(p) = -Σ p_i * log(p_i)
  - Margin: 1 - (p_max1 - p_max2)
  - Least confidence: 1 - p_max

- **Report template** with all sections (see below)

### 8. `.opencode/skills/active-learning/scripts/template_train_classifier.py` (CREATE)

Template with these patterns:

| Function | Purpose |
|---|---|
| `build_tfidf_pipeline(max_features=5000, ngram_range=(1,2), C=1.0)` | sklearn Pipeline with TfidfVectorizer → LogisticRegression |
| `train_classifier(X_train, y_train, pipeline)` | Fit pipeline, return fitted model |
| `evaluate_classifier(model, X_test, y_test, labels)` | Return dict: accuracy, f1_macro, f1_weighted, per_class {precision, recall, f1} |
| `predict_proba(model, X)` | Return numpy array of class probabilities (n_samples, n_classes) |
| `encode_labels(y, label_list)` | Convert string labels to integers, return encoded array and mapping |

Docstring: "This is a reference template — not a runnable CLI script. The agent should adapt these patterns when training classifiers for active learning."

### 9. `.opencode/skills/active-learning/scripts/template_uncertainty.py` (CREATE)

Template with these patterns:

| Function | Purpose |
|---|---|
| `entropy_scores(probabilities)` | Per-sample Shannon entropy: -Σ p_i * log(p_i + ε) |
| `margin_scores(probabilities)` | Per-sample margin: 1 - (p_max1 - p_max2) |
| `least_confidence_scores(probabilities)` | Per-sample: 1 - max(p) |
| `select_top_k(scores, pool_indices, k)` | Return indices of top-k highest uncertainty |
| `select_random(pool_indices, k, seed=42)` | Random selection baseline |
| `compute_uncertainty(probabilities, strategy)` | Dispatch to entropy/margin/least_confidence based on strategy string |

Docstring: "This is a reference template — not a runnable CLI script. The agent should adapt these patterns when computing uncertainty scores for sample selection."

### 10. `.opencode/skills/active-learning/scripts/template_visualize.py` (CREATE)

Template with these patterns:

| Function | Purpose |
|---|---|
| `plot_learning_curve(iterations_df, save_path)` | Dual-line plot: accuracy and F1 vs iteration number |
| `plot_train_size_curve(iterations_df, save_path)` | Accuracy and F1 vs labeled set size (canonical AL learning curve) |
| `plot_baseline_comparison(baseline_metrics, al_metrics, save_path)` | Side-by-side bar chart: baseline vs AL final accuracy + F1 |
| `save_figure(fig, path, dpi=150)` | Save with tight_layout, ensure parent dir exists |

Docstring: "This is a reference template — not a runnable CLI script. The agent should adapt these patterns when generating learning curve visualizations."

## Output Structure

```
<session_dir>/active-learning/
├── selected_samples.csv     # iteration, original_index, text, predicted_label, ground_truth, uncertainty_score
├── learning_curve.csv       # iteration, train_size, accuracy, f1_macro, f1_weighted
├── model_metrics.json       # baseline vs AL comparison + per-iteration details
├── learning_curve.png       # matplotlib visualization
└── report.md
```

## model_metrics.json Structure

```json
{
  "baseline": {
    "accuracy": 0.72,
    "f1_macro": 0.68,
    "f1_weighted": 0.70,
    "train_size": 150,
    "per_class": {
      "positive": {"precision": 0.75, "recall": 0.70, "f1": 0.72},
      "negative": {"precision": 0.68, "recall": 0.72, "f1": 0.70},
      "neutral": {"precision": 0.65, "recall": 0.62, "f1": 0.63}
    }
  },
  "active_learning_final": {
    "accuracy": 0.85,
    "f1_macro": 0.82,
    "f1_weighted": 0.84,
    "train_size": 400,
    "per_class": {
      "positive": {"precision": 0.88, "recall": 0.83, "f1": 0.85},
      "negative": {"precision": 0.82, "recall": 0.85, "f1": 0.83},
      "neutral": {"precision": 0.78, "recall": 0.75, "f1": 0.76}
    }
  },
  "improvement": {
    "accuracy_delta": 0.13,
    "f1_macro_delta": 0.14,
    "additional_samples": 250
  },
  "iterations": [
    {"iteration": 0, "train_size": 150, "accuracy": 0.72, "f1_macro": 0.68, "f1_weighted": 0.70},
    {"iteration": 1, "train_size": 200, "accuracy": 0.76, "f1_macro": 0.73, "f1_weighted": 0.75},
    {"iteration": 2, "train_size": 250, "accuracy": 0.79, "f1_macro": 0.76, "f1_weighted": 0.78},
    {"iteration": 3, "train_size": 300, "accuracy": 0.82, "f1_macro": 0.79, "f1_weighted": 0.81},
    {"iteration": 4, "train_size": 350, "accuracy": 0.84, "f1_macro": 0.81, "f1_weighted": 0.83},
    {"iteration": 5, "train_size": 400, "accuracy": 0.85, "f1_macro": 0.82, "f1_weighted": 0.84}
  ]
}
```

## report.md Template

```markdown
# Active Learning Report

## Dataset Summary
- Golden set size: X (from labeled.csv)
- Unlabeled pool size: Y
- Validation split: Z%
- Text column: <name>
- Classes: [list]

## Golden Set Selection
- Total labeled samples from annotation: X
- Golden set size: Y
- Selection rule: agreement-based / all labeled (no original labels)

## Baseline Model (no active learning)
- Train size: X
- Validation size: Y
- Accuracy: X.XX
- F1 (macro): X.XX
- F1 (weighted): X.XX
- Per-class metrics:
| Class | Precision | Recall | F1 |
|---|---|---|---|
| ... | ... | ... | ... |

## Active Learning Configuration
- Strategy: entropy / margin / random
- Batch size: X (user-selected)
- Iterations: Y (user-selected)
- Total additional samples: X × Y = Z

## Learning Curve
| Iteration | Train Size | Accuracy | F1 (macro) | F1 (weighted) |
|---|---|---|---|---|
| 0 (baseline) | 150 | 0.72 | 0.68 | 0.70 |
| 1 | 200 | 0.76 | 0.73 | 0.75 |
| ... | ... | ... | ... | ... |

See learning_curve.png

## Baseline vs Active Learning Comparison
| Metric | Baseline | Active Learning | Delta |
|---|---|---|---|
| Accuracy | 0.72 | 0.85 | +0.13 |
| F1 (macro) | 0.68 | 0.82 | +0.14 |
| F1 (weighted) | 0.70 | 0.84 | +0.14 |
| Train size | 150 | 400 | +250 |

## Selected Samples Summary
- Total samples selected: X
- Per iteration breakdown:
  - Iteration 1: 50 samples (avg uncertainty: X.XX)
  - Iteration 2: 50 samples (avg uncertainty: X.XX)
  - ...

## Key Findings
- Active learning improved F1 by X% using Y additional samples
- Most uncertain samples concentrated in class: ...
- Learning curve shows diminishing returns after iteration X
- Comparison: AL achieved same F1 as baseline with Z% fewer labeled samples
```

## What does NOT change

| File | Reason |
|---|---|
| Collection agent/skill/scripts | No relevance to active learning |
| Quality agent/skill/scripts | No relevance to active learning |
| Annotation templates | Already produce labeled.csv that AL consumes |
| `.env_example` | No new external services needed |
| Existing tests | No API changes to existing scripts |

## Execution order

1. `src/models.py` — add 2 AL fields (schema foundation)
2. `pyproject.toml` — `uv add matplotlib` (dependency)
3. `PROJECT_SPEC.md` — stage 4 + contract (spec update)
4. `AGENTS.md` — agent table + invocation (project rules)
5. `.opencode/agents/orchestrator.md` — remove conditional, add AL step (orchestration)
6. `.opencode/skills/active-learning/scripts/template_train_classifier.py` — create
7. `.opencode/skills/active-learning/scripts/template_uncertainty.py` — create
8. `.opencode/skills/active-learning/scripts/template_visualize.py` — create
9. `.opencode/skills/active-learning/SKILL.md` — create
10. `.opencode/agents/active-learning.md` — create

## Verification

After implementation:
- Run `uv run ruff check .opencode/skills/active-learning/`
- Verify `DataContract` instantiates with new default fields
- Verify contract schema is consistent across PROJECT_SPEC.md, AGENTS.md, orchestrator.md
- Verify agent table in AGENTS.md has all 5 agents
- Verify matplotlib imports work in template_visualize.py
