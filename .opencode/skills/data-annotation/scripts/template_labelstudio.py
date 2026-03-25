"""Template: Export labeled data to LabelStudio JSON format.

This is a reference template — not a runnable CLI script.
The agent should adapt these patterns when exporting annotations
to LabelStudio-compatible JSON.

Label Studio format reference:
https://labelstud.io/guide/tasks#Basic-Label-Studio-JSON-format
"""

import json
from pathlib import Path


# --- Pattern: build a single classification task ---
def build_classification_task(
    row_data: dict,
    label: str,
    confidence: float,
    from_name: str = "label_class",
    to_name: str = "text",
) -> dict:
    """Build a LabelStudio task with a classification pre-annotation.

    Args:
        row_data: Dict with all original columns from the dataset row.
        label: The assigned label value.
        confidence: Confidence score between 0 and 1.
        from_name: Name of the labeling control tag.
        to_name: Name of the object tag being labeled.

    Returns:
        LabelStudio task dict with pre-annotation.
    """
    return {
        "data": row_data,
        "predictions": [
            {
                "result": [
                    {
                        "from_name": from_name,
                        "to_name": to_name,
                        "type": "choices",
                        "value": {
                            "choices": [label],
                        },
                    }
                ],
                "score": confidence,
            }
        ],
    }


# --- Pattern: build task list from labeled DataFrame ---
def build_tasks_from_df(
    df,
    label_col: str,
    confidence_col: str | None = None,
    text_col: str | None = None,
    from_name: str = "label_class",
    to_name: str = "text",
) -> list[dict]:
    """Convert a labeled DataFrame to a list of LabelStudio tasks.

    Args:
        df: DataFrame with labels (and optionally confidences).
        label_col: Column containing the assigned labels.
        confidence_col: Optional column with confidence scores.
        text_col: Optional column used as the to_name target.
        from_name: Name of the labeling control tag.
        to_name: Name of the object tag being labeled.

    Returns:
        List of LabelStudio task dicts.
    """
    tasks = []
    for _, row in df.iterrows():
        row_data = row.to_dict()
        # Remove internal columns from data
        row_data.pop("original_index", None)

        label = str(row[label_col])
        confidence = (
            float(row[confidence_col])
            if confidence_col and confidence_col in row.index
            else 0.8
        )

        task = build_classification_task(
            row_data=row_data,
            label=label,
            confidence=confidence,
            from_name=from_name,
            to_name=to_name,
        )
        tasks.append(task)

    return tasks


# --- Pattern: write LabelStudio JSON ---
def write_labelstudio_json(tasks: list[dict], output_path: str) -> None:
    """Write LabelStudio tasks to a JSON file.

    Args:
        tasks: List of LabelStudio task dicts.
        output_path: Path to write the JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)


# --- Pattern: validate LabelStudio JSON structure ---
def validate_labelstudio_json(tasks: list[dict]) -> list[str]:
    """Validate LabelStudio task structure.

    Args:
        tasks: List of task dicts to validate.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    for i, task in enumerate(tasks):
        if "data" not in task:
            errors.append(f"Task {i}: missing 'data' key")
        if "predictions" not in task:
            errors.append(f"Task {i}: missing 'predictions' key")
            continue
        for j, pred in enumerate(task["predictions"]):
            if "result" not in pred:
                errors.append(f"Task {i}, prediction {j}: missing 'result' key")
                continue
            for k, res in enumerate(pred["result"]):
                if "from_name" not in res:
                    errors.append(
                        f"Task {i}, prediction {j}, result {k}: missing 'from_name'"
                    )
                if "to_name" not in res:
                    errors.append(
                        f"Task {i}, prediction {j}, result {k}: missing 'to_name'"
                    )
                if "type" not in res:
                    errors.append(
                        f"Task {i}, prediction {j}, result {k}: missing 'type'"
                    )
                if "value" not in res:
                    errors.append(
                        f"Task {i}, prediction {j}, result {k}: missing 'value'"
                    )
            if "score" not in pred:
                errors.append(f"Task {i}, prediction {j}: missing 'score'")

    return errors


# --- Pattern: compute agreement with original labels ---
def compute_agreement(
    df,
    original_label_col: str,
    assigned_label_col: str,
) -> dict:
    """Calculate agreement between original and assigned labels.

    Args:
        df: DataFrame with both original and assigned labels.
        original_label_col: Column with original labels.
        assigned_label_col: Column with LLM-assigned labels.

    Returns:
        Dict with overall and per-class agreement stats.
    """
    total = len(df)
    if total == 0:
        return {"overall_pct": 0.0, "per_class": {}}

    matches = (df[original_label_col] == df[assigned_label_col]).sum()
    overall_pct = round(matches / total * 100, 2)

    per_class: dict = {}
    for label in df[original_label_col].unique():
        mask = df[original_label_col] == label
        class_total = mask.sum()
        class_matches = (
            df.loc[mask, original_label_col] == df.loc[mask, assigned_label_col]
        ).sum()
        per_class[str(label)] = {
            "total": int(class_total),
            "agreed": int(class_matches),
            "pct": round(class_matches / class_total * 100, 2)
            if class_total > 0
            else 0.0,
        }

    return {
        "overall_pct": overall_pct,
        "total_labeled": total,
        "matching_labels": int(matches),
        "per_class": per_class,
    }
