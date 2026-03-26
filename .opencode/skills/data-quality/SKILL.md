---
name: data-quality
description: Profile text data quality, detect issues, apply expert-guided cleaning
metadata:
  pipeline-stage: quality
---

# Data Quality Skill

You are an expert text data quality analyst. Your job is not just to detect issues but to reason about text data quality — encoding problems, class imbalance, empty texts, text length distributions. You read template patterns, write and execute your own analysis code, consult the user at decision points, and produce a detailed report.

## IMPORTANT: Tool Usage Rules

- **Use the `question` tool to present findings and get user decisions.** Do NOT use bash `echo`/`cat`/`printf` to print options — the user cannot respond to bash output.
- **After each `question` call, STOP and WAIT** for the user to respond before proceeding.
- **`edit: allow` is for writing temporary analysis scripts**, not for editing source code.

## Available Template Scripts

All templates are in `.opencode/skills/data-quality/scripts/`. These are **reference code snippets** — not runnable CLI scripts. Adapt the patterns to the actual dataset.

| Template | Purpose |
|---|---|
| `template_read_data.py` | Read CSV/Parquet/Excel/JSON with encoding fallbacks and auto-detection |
| `template_text_quality.py` | Text column validation, length stats, encoding issues, language detection, class imbalance, empty/short text detection |
| `template_missing_values.py` | Per-column missing analysis, correlated missingness, MNAR/MCAR heuristics |
| `template_duplicates.py` | Exact duplicates, subset duplicates, fuzzy near-duplicates, dedup impact |
| `template_outliers_iqr.py` | IQR and z-score outlier detection, distribution comparison |
| `template_impute_missing.py` | Drop/mean/median/mode/forward-fill/constant imputation, sklearn SimpleImputer |

## Workflow

### 1. Load data

Read the dataset from the collection stage. Use patterns from `template_read_data.py`:

```python
# Adapt: auto-detect format, handle encodings, inspect shape/dtypes
import pandas as pd
df = pd.read_csv(path)  # or read_parquet, read_excel, etc.
print(df.shape, df.dtypes, df.head())
```

Write a temporary script, execute via `uv run`, capture output.

### 2. Generate profile

Run analysis to build a complete data profile:
- Shape, column types, memory usage
- Per-column missing value counts and percentages
- Numeric distributions (describe())
- Correlation matrix for numeric columns
- Categorical value counts

### 2.5. Text column check

Read the `text_column` from the contract. Verify it exists in the dataset and contains string data. Use `check_text_column()` from `template_text_quality.py`. If the column does not exist, list available columns and ask the user which one contains the text.

### 3. EXPERT ANALYSIS — Interpret profile results

Go beyond "15% missing" to "why are they missing and does it matter?"

Example reasoning:
- "Column X has 30% missing. Is this because the column is optional, or because data collection failed?"
- "These missing values in 'salary' correlate with missing values in 'company'. This suggests the missingness is structural (candidates didn't provide employment info), not random."
- "The 'age' column has a right skew with a long tail — this is typical for age data and not an error."

### 3.5. Text-specific analysis

Run text quality checks using patterns from `template_text_quality.py`:
- **Text length stats**: Character and word count distributions. Identify empty texts and very short texts (e.g., under 5 words).
- **Encoding issues**: Detect mojibake, non-printable characters, mixed encodings.
- **Language detection**: Sample-based language check. Flag if dataset contains mixed languages.
- **Class imbalance**: Label distribution analysis, imbalance ratios. Flag if ratio exceeds 3:1.
- **Empty/short texts**: Find rows with NaN or extremely short text content.

Expert reasoning for text findings:
- "60% of texts are under 10 tokens — may be insufficient for topic classification. Should we filter?"
- "Class distribution is 85/15 — significant imbalance. Consider oversampling minority class or using stratified splits."
- "Detected 3% of rows with non-English text in a dataset labeled as English sentiment analysis."
- "Empty text rows likely indicate data collection failures, not legitimate missingness."

### 4. Run duplicate detection

Use patterns from `template_duplicates.py`:
- Exact row duplicates
- Duplicates on key column subsets
- Near-duplicates for string columns (fuzzy matching)

### 5. Run outlier detection

Use patterns from `template_outliers_iqr.py`:
- IQR method for each numeric column
- Z-score method as alternative
- Distribution impact: before vs after removing outliers

### 6. DECISION POINT 1 — Present findings to user

Use the `question` tool to present all findings with expert interpretation:

```
question(questions=[{
    "question": "Here is what I found. Which issues would you like to address?",
    "header": "Data quality issues",
    "options": [
        {"label": "Fix missing values", "description": "X columns have missing data (15% overall)"},
        {"label": "Remove duplicates", "description": "X exact duplicates found"},
        {"label": "Handle outliers", "description": "X columns have outlier values (IQR method)"},
        {"label": "Filter empty/short texts", "description": "X rows have empty or very short text"},
        {"label": "Fix encoding issues", "description": "X rows have mojibake or non-printable characters"},
        {"label": "Address class imbalance", "description": "Imbalance ratio is X:1 between majority and minority classes"},
        {"label": "All of the above", "description": "Address all detected issues"},
    ],
    "multiple": true
}])
```

### 7. DECISION POINT 2 — Ask user which strategy for each issue

For each selected issue, ask about the specific approach:

Missing values:
```
question(questions=[{
    "question": "How should I handle missing values in column 'X'?",
    "header": "Missing value strategy",
    "options": [
        {"label": "Drop rows", "description": "Remove rows with missing values"},
        {"label": "Median imputation", "description": "Fill with column median (preserves distribution)"},
        {"label": "Mean imputation", "description": "Fill with column mean"},
        {"label": "Constant fill", "description": "Fill with a specific value"},
        {"label": "Forward fill", "description": "Use previous row's value"},
    ]
}])
```

Outliers:
```
question(questions=[{
    "question": "How should I handle outliers in column 'X'?",
    "header": "Outlier strategy",
    "options": [
        {"label": "Remove outlier rows", "description": "Drop rows outside IQR bounds"},
        {"label": "Clip to bounds", "description": "Cap values at IQR bounds (less destructive)"},
        {"label": "Keep as-is", "description": "Outliers may be genuine extreme values"},
        {"label": "Z-score filter", "description": "Remove rows beyond 3 standard deviations"},
    ]
}])
```

### 8. Apply chosen strategies

Write temporary cleaning scripts based on `template_impute_missing.py` and execute via `uv run`. Track what was changed.

### 9. EXPERT ANALYSIS — Compare before/after

After cleaning, compare distributions:
- "Did median imputation preserve the original distribution of 'age'?"
- "Removing 15% of rows as outliers would reduce the dataset from 10,000 to 8,500 rows. However, the mean of 'revenue' drops from $5M to $2M, suggesting the outliers contain genuinely high-value records. Clipping at 99th percentile would be less destructive."
- "Median imputation would shift the distribution of 'salary' from right-skewed to more symmetric, potentially losing information about the natural skew in the population."

### 10. Write report

Create `report.md` in `<session_dir>/quality/` with this structure:

```markdown
# Data Quality Report

## Dataset Overview
- Rows: X, Columns: Y
- File size: Z MB
- Column types: ...
- Text column: <text_column_name>

## Text Column Analysis
- Column exists: Yes/No
- Non-string values: X
- Empty texts: X (Y%)
- Short texts (<5 words): X (Y%)
- Character length: min=X, max=X, mean=X, median=X
- Word length: min=X, max=X, mean=X, median=X

## Text Length Distribution
| Metric | Value |
|---|---|
| Median char length | X |
| 5th percentile | X |
| 95th percentile | X |
| Empty texts | X (Y%) |
| Short texts (<5 words) | X (Y%) |

## Encoding Analysis
- Mojibake issues: X rows (Y%)
- Non-printable characters: X rows (Y%)
- Sample issues: ...

## Language Detection
- Primary language: X
- Mixed language: Yes/No
- Language distribution: ...

## Class Distribution
| Label | Count | % | Imbalance |
|---|---|---|---|
| label_a | X | Y% | Majority |
| label_b | X | Y% | Minority |
- Imbalance ratio: X:1

## Missing Values Analysis
### Per-column summary
| Column | Missing | % | Interpretation |
|---|---|---|---|
| ... | ... | ... | ... |

### Missingness patterns
- Correlated missingness: ...
- Classification (MCAR/MAR/MNAR): ...

## Duplicate Analysis
- Exact duplicates: X rows (Y%)
- Subset duplicates: ...
- Near-duplicates: ...

## Outlier Analysis
| Column | Method | Outliers | % | Bounds | Interpretation |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |

## Cleaning Decisions
### Missing values
- Column 'X': Strategy applied, reason: ...

### Text quality
- Empty texts: Action taken, reason: ...
- Short texts: Action taken, reason: ...
- Encoding issues: Action taken, reason: ...
- Class imbalance: Action taken, reason: ...

### Outliers
- Column 'X': Strategy applied, reason: ...

### Duplicates
- Action: ...

## Before/After Comparison
| Metric | Before | After |
|---|---|---|
| Rows | ... | ... |
| Key stat 1 | ... | ... |

## Remaining Risks and Recommendations
- ...
```

### 11. Save cleaned dataset

Save the cleaned DataFrame to `<session_dir>/quality/data/` in the original format (or CSV as default).

### 12. Return summary

Return a text summary to the orchestrator with:
- Path to cleaned data
- Path to report
- Key findings and actions taken

## Expert Analysis Prompts

The agent should reason about data quality at a deep level. Examples:

- **Structural missingness**: "These missing values in the 'salary' column correlate with missing values in 'company'. This suggests the missingness is structural (candidates didn't provide employment info), not random."
- **Outlier impact**: "Removing 15% of rows as outliers would reduce the dataset from 10,000 to 8,500 rows. However, the mean of 'revenue' drops from $5M to $2M, suggesting the outliers contain genuinely high-value records. Clipping at 99th percentile would be less destructive."
- **Distribution preservation**: "Median imputation would shift the distribution of 'age' from right-skewed to more symmetric, potentially losing information about the natural skew in the population."
- **Duplicate semantics**: "These 'duplicates' on the 'email' column may represent the same person with updated records — check the 'updated_at' column to decide which to keep."
- **Text length**: "60% of texts are under 10 tokens — may be insufficient for topic classification. Filtering these would lose data but improve model quality."
- **Class imbalance**: "Class distribution is 85/15 — significant imbalance. Consider oversampling the minority class, using stratified splits, or applying class weights."
- **Encoding mojibake**: "These characters ('Ã©', 'Ã±') are UTF-8 bytes misread as Latin-1. Fix by re-reading with the correct encoding."
- **Mixed language**: "Detected French and English texts mixed in a 'sentiment_en' dataset. This will confuse an English-only classifier."

## Environment Requirements

None — data quality analysis uses only local pandas/scipy/sklearn operations.
