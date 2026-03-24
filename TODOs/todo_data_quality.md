# TODO: Data Quality Agent

## Overview

Implement the second pipeline stage — data quality analysis. This agent acts as an **expert data analyst**, not just a script runner. It reads template patterns, writes and executes its own analysis code, reasons about findings (e.g., "are these missing values meaningful or just bad data?"), consults the user at decision points, and produces a detailed `report.md` explaining every step and decision.

All 5 scripts are **templates** (code snippets for the agent to reference), not fully implemented CLI scripts. The agent adapts and executes its own versions.

## Files to create (7 total)

### 1. Scripts (5 template files in `.opencode/skills/data-quality/scripts/`)

All templates follow the same pattern as `template_scrape_web.py` from data-collection: heavily commented code snippets demonstrating a pattern. The agent reads these, adapts them to the actual dataset, and executes via `uv run`.

#### `template_read_data.py` — Reading data into pandas

Demonstrates patterns for:
- Reading CSV: `pd.read_csv(path)`, handling encodings (`utf-8`, `latin-1`, `iso-8859-1`), delimiters, quoting
- Reading Parquet: `pd.read_parquet(path)`, selecting columns
- Reading Excel: `pd.read_excel(path, sheet_name=...)`, multi-sheet handling
- Auto-detection: try formats based on file extension, fallback chain
- Initial inspection: `df.shape`, `df.dtypes`, `df.head()`, `df.info()`

#### `template_missing_values.py` — Analyzing missing values

Demonstrates patterns for:
- Per-column missing count and percentage: `df.isnull().sum()`, `df.isnull().mean()`
- Visualizing missing patterns: which columns are missing together (correlated missingness)
- Classifying missingness types: MCAR (missing completely at random), MAR (missing at random), MNAR (missing not at random)
- Checking if missing values cluster in rows: `df[df['col'].isnull()].describe()` vs `df[df['col'].notnull()].describe()`
- Domain reasoning prompts: when missing = "not applicable" vs "not recorded" vs "error"

#### `template_duplicates.py` — Finding duplicates

Demonstrates patterns for:
- Exact row duplicates: `df[df.duplicated()]`, `df.duplicated().sum()`
- Duplicates on subset of columns: `df[df.duplicated(subset=['col1', 'col2'])]`
- Near-duplicates (fuzzy): comparing string columns with `SequenceMatcher` or simple ratio
- Deciding which duplicate to keep: `df.drop_duplicates(keep='first'|'last'|False)`
- Impact analysis: what percentage of data is duplicated

#### `template_outliers_iqr.py` — Detecting outliers with IQR

Demonstrates patterns for:
- IQR calculation: `Q1 = df[col].quantile(0.25)`, `Q3 = df[col].quantile(0.75)`, `IQR = Q3 - Q1`
- Outlier bounds: `lower = Q1 - 1.5 * IQR`, `upper = Q3 + 1.5 * IQR`
- Counting and listing outliers per numeric column
- Z-score alternative: `scipy.stats.zscore()`
- Distribution impact analysis: comparing distributions with/without outliers (`df.describe()` before vs after)
- Expert reasoning: "do these outliers represent real extreme values or data entry errors?"

#### `template_impute_missing.py` — Imputing missing values

Demonstrates patterns for:
- Drop rows: `df.dropna(subset=[cols])`
- Mean/median/mode imputation: `df[col].fillna(df[col].median())`
- Forward/backward fill: `df[col].ffill()`, `df[col].bfill()`
- Constant fill: `df[col].fillna(0)`, `df[col].fillna('Unknown')`
- sklearn `SimpleImputer` for multi-column imputation
- Distribution preservation check: compare `df[col].describe()` before and after imputation
- Expert reasoning: "does median imputation preserve the relationship between columns?"

### 2. `.opencode/skills/data-quality/SKILL.md`

Frontmatter:
```yaml
name: data-quality
description: Profile data quality, detect issues, apply expert-guided cleaning
metadata:
  pipeline-stage: quality
```

Body contains:
- Role definition: "You are an expert data quality analyst. Your job is not just to detect issues but to reason about their causes and implications."
- Available template scripts with descriptions
- **Workflow steps**:
  1. Load data (use `template_read_data.py` pattern)
  2. Generate profile (shape, dtypes, missing, distributions, correlations)
  3. **EXPERT ANALYSIS**: Interpret profile results — e.g., "Column X has 30% missing. Is this because the column is optional, or because data collection failed?"
  4. Run duplicate detection
  5. Run outlier detection
  6. **DECISION POINT 1**: Present findings to user with expert interpretation, ask which issues to address
  7. **DECISION POINT 2**: For each issue, ask the user which strategy to apply
  8. Apply chosen strategies (write and execute scripts)
  9. **EXPERT ANALYSIS**: Compare before/after — "did cleaning preserve the original data distribution? Are there new patterns introduced?"
  10. Write report.md
  11. Save cleaned dataset to `<session_dir>/quality/data/`
  12. Return summary with path to cleaned data and report

- **Expert analysis prompts** — examples of the kind of reasoning the agent should do:
  - "These missing values in the 'salary' column correlate with missing values in 'company'. This suggests the missingness is structural (candidates didn't provide employment info), not random."
  - "Removing 15% of rows as outliers would reduce the dataset from 10,000 to 8,500 rows. However, the mean of 'revenue' drops from $5M to $2M, suggesting the outliers contain genuinely high-value records. Clipping at 99th percentile would be less destructive."
  - "Median imputation would shift the distribution of 'age' from right-skewed to more symmetric, potentially losing information about the natural skew in the population."

- **Report.md template** — what the report should contain:
  - Dataset overview (shape, column types, file size)
  - Missing values analysis (per column, patterns, expert interpretation)
  - Duplicate analysis (count, affected columns, expert interpretation)
  - Outlier analysis (per numeric column, method used, expert interpretation)
  - Cleaning decisions (what was done and why)
  - Before/after comparison (key statistics, distribution changes)
  - Remaining risks and recommendations

### 3. `.opencode/agents/data-quality.md`

Frontmatter:
```yaml
description: Expert data quality analyst — profiles, detects issues, reasons about causes, applies cleaning
mode: subagent
temperature: 0.1
permission:
  bash:
    "*": allow
  edit: allow  # needs edit to write temporary analysis scripts
```

Body:
- Role: "You are an expert data quality analyst. Your value is not in running scripts, but in interpreting results and reasoning about data."
- Instructions:
  1. Load skill
  2. Read the dataset
  3. Profile and analyze (write temporary scripts based on templates, execute via bash)
  4. Reason about findings — go beyond "15% missing" to "why are they missing and does it matter?"
  5. Present findings to user with expert framing
  6. Apply user-approved cleaning
  7. Verify cleaning preserved data integrity
  8. Save cleaned dataset to `<session_dir>/quality/data/`
  9. Write comprehensive report.md
  10. Return summary with path to cleaned data and report

Note: `edit: allow` is needed because the agent must write temporary analysis scripts to the workspace, not because it edits source code.

### 4. `tests/test_data_quality.py`

Integration tests:
- Template scripts are importable and have valid Python syntax
- Agent definition is valid (frontmatter parses)
- SKILL.md has valid frontmatter with correct `name`
- (Optional, needs test data) Profile a small CSV and verify JSON output

## What was done

All 7 files created, 41 tests passing, ruff clean.

### Files created

| # | File | Status |
|---|---|---|
| 1 | `.opencode/skills/data-quality/scripts/template_read_data.py` | ✓ |
| 2 | `.opencode/skills/data-quality/scripts/template_missing_values.py` | ✓ |
| 3 | `.opencode/skills/data-quality/scripts/template_duplicates.py` | ✓ |
| 4 | `.opencode/skills/data-quality/scripts/template_outliers_iqr.py` | ✓ |
| 5 | `.opencode/skills/data-quality/scripts/template_impute_missing.py` | ✓ |
| 6 | `.opencode/skills/data-quality/SKILL.md` | ✓ |
| 7 | `.opencode/agents/data-quality.md` | ✓ |
| 8 | `tests/test_data_quality.py` | ✓ |

### Dependencies added

`numpy`, `scipy`, `scikit-learn`, `pyyaml` added to `pyproject.toml`.

### Test results

- 41/41 tests passing
- Template syntax compilation (5 tests)
- Template content patterns (18 tests)
- SKILL.md frontmatter validation (8 tests)
- Agent definition validation (10 tests)

## Execution order

1. 5 template scripts — create all at once (no dependencies between them)
2. `SKILL.md` — references templates by name, defines workflow and expert analysis prompts
3. `data-quality.md` agent — references skill
4. Tests — verify structure and syntax

