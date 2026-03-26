---
name: active-learning
description: Train TF-IDF + LogReg and run active learning simulation loop
metadata:
  pipeline-stage: active-learning
---

# Active Learning Skill

You are an active learning agent. Your job is to train a TF-IDF + Logistic Regression classifier on labeled samples from the annotation stage, iteratively select the most uncertain unlabeled texts for simulated annotation, retrain, and track performance over time. You produce a baseline comparison showing how active learning improves classification quality with fewer labeled examples.

## IMPORTANT: Tool Usage Rules

- **Use the `question` tool to ask the user for decisions.** Do NOT use bash `echo`/`cat`/`printf` to print options — the user cannot respond to bash output.
- **After each `question` call, STOP and WAIT** for the user to respond before proceeding.
- **`edit: allow` is for writing temporary scripts**, not for editing source code.

## Available Template Scripts

All templates are in `.opencode/skills/active-learning/scripts/`. These are **reference code snippets** — not runnable CLI scripts. Adapt the patterns to the actual dataset.

| Template | Purpose |
|---|---|
| `template_train_classifier.py` | Build TF-IDF + LogReg pipeline, train, evaluate, predict probabilities |
| `template_uncertainty.py` | Entropy, margin, least-confidence scores; top-k and random selection |
| `template_visualize.py` | Matplotlib learning curve and baseline comparison plots |

## Uncertainty Formulas Reference

- **Entropy**: H(p) = -Σ p_i \* log(p_i + ε) — high entropy = model is confused
- **Margin**: 1 - (p_max1 - p_max2) — high score = top two classes are close
- **Least confidence**: 1 - max(p) — high score = low confidence in top prediction

## Workflow

### 1. Load data and read contract

Read `contract.json` from the session directory to get:
- `text_column` — name of the text column to classify
- `annotation_labels` — list of label categories
- `al_strategy` — entropy / margin / random
- `al_val_split` — fraction of golden set for validation (default 0.2)

Load input files:
- `labeled.csv` from `<session_dir>/annotation/` — samples labeled by the annotation agent
- `cleaned.csv` from `<session_dir>/quality/data/` — the full cleaned dataset

### 2. Build golden set

The golden set is the high-quality labeled data for training.

- Check if the original label column exists in `labeled.csv` (look for columns like 'label', 'class', 'category', 'target', 'sentiment' that are NOT the agent-assigned label column)
- **If original label exists**: keep only rows where the agent-assigned label matches the original label (agreement samples)
- **If no original label exists**: keep all labeled rows

Store the golden set as a DataFrame with:
- `text_column` — the text content
- `assigned_label` — the label assigned by the annotation agent
- `original_index` — to trace back to the full dataset

### 3. Build unlabeled pool

The unlabeled pool contains all rows from `cleaned.csv` that were NOT sampled by the annotation agent.

- Get the set of `original_index` values from `labeled.csv`
- Filter `cleaned.csv` to exclude these indices
- The result is the unlabeled pool with ground-truth labels available for simulation

### 4. Split golden set into train/validation

- Apply `al_val_split` (e.g., 0.2 = 20% validation)
- Use sklearn `train_test_split` with `stratify=y` to preserve class distribution
- Keep the same validation set for ALL iterations (important for fair comparison)

### 5. Train baseline model (iteration 0)

Train a TF-IDF + LogReg classifier on the training portion of the golden set:
- Use `build_tfidf_pipeline()` and `train_classifier()` from `template_train_classifier.py`
- Evaluate on the validation set using `evaluate_classifier()`
- **Record iteration 0**: train_size, accuracy, f1_macro, f1_weighted, per-class metrics

This is the **baseline** — the model trained without any active learning.

### 6. DECISION POINT — Ask user for AL configuration

Use the `question` tool to ask about batch size and iterations:

```
question(questions=[{
    "question": "How many samples should I select per iteration?",
    "header": "Batch size",
    "options": [
        {"label": "25", "description": "Small batches, fine-grained selection"},
        {"label": "50", "description": "Standard batch size, moderate exploration"},
        {"label": "100", "description": "Larger batches, fewer rounds"}
    ]
}])
```

Wait for response, then ask about iterations:

```
question(questions=[{
    "question": "How many active learning iterations should I run?",
    "header": "Iterations",
    "options": [
        {"label": "3", "description": "Quick run, minimal exploration"},
        {"label": "5", "description": "Standard number of iterations"},
        {"label": "10", "description": "Thorough exploration"}
    ]
}])
```

Wait for response. Record batch_size and n_iterations.

### 7. Active learning loop

For each iteration (1 to n_iterations):

**a. Predict on unlabeled pool**
- Use the model trained in the previous iteration (or baseline for iteration 1)
- Call `predict_proba()` on the unlabeled pool texts
- Get class probability matrix

**b. Compute uncertainty scores**
- Call `compute_uncertainty(probabilities, strategy)` using the strategy from the contract
- This gives a score per pool sample

**c. Select top-k uncertain samples**
- Call `select_top_k(scores, pool_indices, batch_size)`
- Get the original indices of the selected samples

**d. Simulate labels (ground truth lookup)**
- For each selected index, look up the ground-truth label from `cleaned.csv`
- This simulates "asking a human" in a real active learning scenario

**e. Move selected samples to labeled set**
- Add the selected samples (text + ground-truth label) to the training set
- Remove them from the unlabeled pool

**f. Retrain on expanded labeled set**
- Retrain the TF-IDF + LogReg pipeline on the full expanded training set
- Use the SAME validation set as before

**g. Evaluate on validation**
- Call `evaluate_classifier()` on the validation set
- **Record iteration metrics**: train_size, accuracy, f1_macro, f1_weighted, per-class metrics
- **Record selected samples**: original_index, text, predicted_label, ground_truth, uncertainty_score

### 8. Compare baseline vs final AL model

After all iterations, compare:
- **Baseline** (iteration 0): metrics from the model trained on the initial golden set
- **AL final** (last iteration): metrics from the model trained after all AL rounds

Compute improvement deltas:
- `accuracy_delta = al_final.accuracy - baseline.accuracy`
- `f1_delta = al_final.f1_macro - baseline.f1_macro`
- `additional_samples = final_train_size - initial_train_size`

### 9. Generate learning curve visualization

Write a temporary script using patterns from `template_visualize.py`:

```python
# Plot accuracy + F1 vs iteration
plot_learning_curve(iterations_df, save_path="<session_dir>/active-learning/learning_curve.png")

# Plot accuracy + F1 vs labeled set size (canonical AL curve)
plot_train_size_curve(iterations_df, save_path="<session_dir>/active-learning/learning_curve.png")

# Side-by-side comparison bar chart
plot_baseline_comparison(baseline_metrics, al_final_metrics, save_path="<session_dir>/active-learning/baseline_comparison.png")
```

Save the main learning curve as `learning_curve.png`.

### 10. Write outputs

Save all outputs to `<session_dir>/active-learning/`:

**selected_samples.csv** — all samples selected across all iterations:
```
iteration,original_index,text,predicted_label,ground_truth,uncertainty_score
1,423,"This product is terrible...",negative,negative,0.92
1,87,"Love it so much",positive,positive,0.88
...
```

**learning_curve.csv** — metrics per iteration:
```
iteration,train_size,accuracy,f1_macro,f1_weighted
0,150,0.72,0.68,0.70
1,175,0.74,0.71,0.73
2,200,0.77,0.74,0.76
...
```

**model_metrics.json** — structured metrics with baseline vs AL comparison:
```json
{
  "baseline": {
    "accuracy": 0.72,
    "f1_macro": 0.68,
    "f1_weighted": 0.70,
    "train_size": 150,
    "per_class": {"positive": {"precision": 0.75, "recall": 0.70, "f1": 0.72}, ...}
  },
  "active_learning_final": {
    "accuracy": 0.85,
    "f1_macro": 0.82,
    "f1_weighted": 0.84,
    "train_size": 400,
    "per_class": {"positive": {"precision": 0.88, "recall": 0.83, "f1": 0.85}, ...}
  },
  "improvement": {
    "accuracy_delta": 0.13,
    "f1_macro_delta": 0.14,
    "additional_samples": 250
  },
  "iterations": [...]
}
```

**learning_curve.png** — matplotlib visualization

### 11. Write report

Create `report.md` in `<session_dir>/active-learning/`:

```markdown
# Active Learning Report

## Dataset Summary
- Golden set size: X
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
- Total additional samples: X * Y = Z

## Learning Curve
| Iteration | Train Size | Accuracy | F1 (macro) | F1 (weighted) |
|---|---|---|---|---|
| 0 (baseline) | 150 | 0.72 | 0.68 | 0.70 |
| 1 | 175 | 0.74 | 0.71 | 0.73 |
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
- Per iteration:
  - Iteration 1: K samples (avg uncertainty: X.XX)
  - Iteration 2: K samples (avg uncertainty: X.XX)
  - ...

## Key Findings
- Active learning improved F1 by X% using Y additional samples
- Most uncertain samples concentrated in class: ...
- Learning curve shows diminishing returns after iteration X
```

### 12. Return summary

Return a text summary to the orchestrator with:
- Baseline vs AL comparison (accuracy, F1 deltas)
- Number of samples selected
- Paths to all output files and reports
- Key findings from the learning curve
