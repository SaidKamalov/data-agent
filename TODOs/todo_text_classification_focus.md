# TODO: Narrow System to Text Classification Focus

## Overview

Narrow DataAgent from general-purpose data pipeline to a **text classification** system covering narrative classification, topic classification, sentiment analysis, and similar tasks. This affects all agents, skills, models, and documentation. No new dependencies needed.

## Files to create/modify (11 total)

### 1. `PROJECT_SPEC.md` — Domain narrowing

| Section | Change |
|---|---|
| Overview | Replace "data exploration, analysis, and annotation" with "text data collection, quality analysis, and classification annotation" |
| Pipeline stages | Update descriptions: "Search and download **text classification** datasets", "Profile **text-related quality issues**", "Sample and **classify text**" |
| Data Contract schema | Simplify `annotation_task` enum to just `"classification"`. Add new field `text_column: str` (name of the text column to classify). Update `annotation_labels` description to reference classification categories |
| End-to-end flow | Replace European startup funding example with a text classification example (e.g., sentiment analysis, topic classification, fake review detection) |
| Stages 4-5 | Keep reserved, add note that they are outside current text classification scope |

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
  "annotation_labels": ["list of label categories if known"]
}
```

### 2. `AGENTS.md` — Purpose descriptions + schema update

| Section | Change |
|---|---|
| Agent purpose table | Add "text classification" to each agent's purpose |
| Contract schema | Same changes as PROJECT_SPEC — add `text_column`, simplify `annotation_task` |

### 3. `.opencode/agents/orchestrator.md` — Questions + schema

| Area | Change |
|---|---|
| Contract schema block | Update to match new schema (add `text_column`, simplify `annotation_task`) |
| Clarifying questions (step 2) | Add: "What is the text column name?" and "What classification categories do you have in mind?" (e.g., sentiment: positive/negative/neutral, topic: politics/sports/tech). Remove NER/regression from annotation options |
| Question framing | Change "What columns of interest?" to "What text field should be classified?" |
| Workflow step 4 | Update contract creation example to include `text_column` |

### 4. `.opencode/agents/data-collection.md` — Description update

| Area | Change |
|---|---|
| Description (frontmatter) | "Searches and downloads **text classification** datasets from Kaggle, HuggingFace, and web" |
| Agent instructions | Add guidance to prioritize datasets that have a clear text column + label column |

### 5. `.opencode/skills/data-collection/SKILL.md` — Search hints + text filter

| Section | Change |
|---|---|
| Description (frontmatter) | "Search and download **text classification** datasets from Kaggle, HuggingFace, and web sources" |
| Step 2 search queries | Suggest appending "text classification" to search queries (e.g., `search_kaggle.py --query "sentiment analysis dataset"`) |
| Step 4 filter | Add text-specific filter: when presenting options, note which datasets have a clear text column + label column. Prefer datasets where description mentions text content |
| Scripts section | No changes to scripts themselves — they accept arbitrary `--query` args |

### 6. `.opencode/agents/data-quality.md` — Text-specific analysis

| Area | Change |
|---|---|
| Description (frontmatter) | "Expert **text** data quality analyst — profiles text characteristics, detects issues, applies cleaning" |
| Instructions step 3 | Add: "Check the text column exists (from contract `text_column`), analyze text length distributions, detect encoding issues, check for empty/short texts, analyze class balance in labels" |
| Instructions step 4 (expert reasoning) | Add text-specific examples: "60% of texts are under 10 tokens — may be insufficient for topic classification", "Class distribution is 85/15 imbalanced", "3% of rows have non-English text" |
| Instructions step 5 | Add text-specific options to the decision point question: "Filter short texts", "Address class imbalance", "Remove non-language-matching rows" |
| Return summary | Add text-specific action descriptions (e.g., "Filtered 500 rows with empty text column") |

### 7. `.opencode/skills/data-quality/SKILL.md` — New text sections + template ref

| Section | Change |
|---|---|
| Description (frontmatter) | "Profile **text** data quality, detect issues, apply expert-guided cleaning" |
| Available templates table | Add row: `template_text_quality.py` — Text length, encoding, language, class balance, empty/short text detection |
| New step 2.5: Text column check | Verify the expected text column from contract `text_column` exists, confirm it contains string data |
| New step 3.5: Text-specific analysis | Run text length profiling, encoding checks, language detection, class balance analysis |
| New DECISION POINT | Present text-specific findings between existing decision points: empty texts, class imbalance, encoding issues, short text filtering |
| Expert analysis prompts | Add text-specific reasoning examples (see step 6 above) |
| Report template | Add text-specific sections: "Text Column Analysis", "Class Distribution", "Language Detection", "Text Length Distribution" |

### 8. **NEW** `.opencode/skills/data-quality/scripts/template_text_quality.py`

New template with these patterns:

| Pattern | Purpose |
|---|---|
| `text_length_stats(df, text_col)` | Character and word count distributions, length outliers (empty texts, very long texts) |
| `detect_encoding_issues(df, text_col)` | Mojibake detection, non-printable characters, mixed encodings |
| `detect_language_sample(df, text_col, sample_size=100)` | Sample-based language detection using `langdetect` (import try/except — if not installed, report it) |
| `class_imbalance(df, label_col)` | Label distribution, imbalance ratios, majority/minority class identification |
| `find_empty_or_short(df, text_col, min_length=3)` | Rows with empty, NaN, or extremely short text |
| `check_text_column(df, text_col)` | Validate column exists and contains string data, report non-string values |

This is a **template** (not a CLI script) — the agent adapts patterns to the actual dataset. If `langdetect` is not installed, the agent can fall back to simple heuristics or skip language detection.

### 9. `.opencode/agents/annotation.md` — Text classification focus

| Area | Change |
|---|---|
| Description (frontmatter) | "Samples and classifies **text** data, exports LabelStudio JSON with pre-annotations" |
| Instructions step 4d (labeling) | Add guidance: use contract `text_column` to identify which column contains the text. Read the text content, reason about the label. The `to_name` in LabelStudio export should reference `text_column` |
| Instructions step 4a (read and inspect) | Add: "Verify the text column exists and contains readable text" |
| Output structure | No change needed |

### 10. `.opencode/skills/data-annotation/SKILL.md` — Text classification examples

| Section | Change |
|---|---|
| Description (frontmatter) | "Sample data and **classify text**, export LabelStudio JSON with pre-annotations" |
| Labeling guidance (step 3d) | Change example from "fraudulent review" to a clearer text classification example (e.g., sentiment: positive/negative, topic: sports/politics/tech) |
| Labeling guidance | Add: "Use `contract.text_column` as the `to_name` in LabelStudio export" |
| LabelStudio format section | Update `to_name` examples from `"text"` to the actual text column name |
| Sampling (step 3c) | Clarify that stratification uses the label/class distribution |

### 11. `src/models.py` — Add text_column field

| Change | Detail |
|---|---|
| `DataContract.text_column` | Add: `text_column: str` — the column containing text to classify |
| `DataContract.annotation_task` | Add docstring note: currently only `"classification"` is supported |

## What does NOT change

| File | Why no change |
|---|---|
| Search scripts (`search_kaggle.py`, `search_huggingface.py`, etc.) | Accept arbitrary `--query` args — agent provides text-specific queries |
| Download scripts (`download_kaggle.py`, `download_huggingface.py`) | Generic download — no text-specific logic needed |
| Quality templates (`template_read_data.py`, `template_missing_values.py`, etc.) | Still relevant for text data — text datasets have missing values, duplicates, etc. |
| Annotation templates (`template_sample.py`, `template_labelstudio.py`) | Already classification-focused — work as-is |
| `.env_example`, `pyproject.toml`, `.gitignore` | No new dependencies needed for text quality checks (pandas string ops cover it) |
| Tests | Existing tests still pass — no API changes to existing scripts |

## Execution order

1. `src/models.py` — add `text_column` field first (everything else references the schema)
2. `PROJECT_SPEC.md` — update spec (other docs reference it)
3. `AGENTS.md` — update project rules
4. `orchestrator.md` — update contract schema + questions
5. `data-collection.md` + `data-collection/SKILL.md` — search guidance updates
6. **NEW** `data-quality/scripts/template_text_quality.py` — create the template
7. `data-quality.md` + `data-quality/SKILL.md` — text-specific quality analysis
8. `annotation.md` + `data-annotation/SKILL.md` — text classification labeling

## Verification

After implementation:
- Run `uv run ruff check` to verify no lint errors
- Verify all agent markdown files have valid YAML frontmatter
- Verify contract.json schema is consistent across PROJECT_SPEC.md, AGENTS.md, and orchestrator.md
- Existing tests in `tests/test_data_collection.py` should still pass (no API changes)
