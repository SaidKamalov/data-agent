"""Template: Finding duplicates.

This is a reference template — not a runnable CLI script.
The agent should adapt these patterns when detecting duplicate records.
"""

import pandas as pd
from difflib import SequenceMatcher


# --- Pattern: exact row duplicates ---
def exact_duplicates(df: pd.DataFrame) -> dict:
    """Find exact row duplicates.

    Args:
        df: DataFrame to analyze.

    Returns:
        Dict with count, percentage, and sample duplicate rows.
    """
    dup_mask = df.duplicated(keep=False)
    dup_count = int(df.duplicated().sum())
    total = len(df)

    return {
        "duplicate_count": dup_count,
        "duplicate_pct": round(dup_count / total * 100, 2) if total > 0 else 0.0,
        "rows_affected": int(dup_mask.sum()),
        "sample": df[df.duplicated(keep="first")].head(5).to_dict(orient="records"),
    }


# --- Pattern: duplicates on subset of columns ---
def subset_duplicates(df: pd.DataFrame, columns: list[str]) -> dict:
    """Find duplicates based on a subset of columns.

    Args:
        df: DataFrame to analyze.
        columns: Column names to check for duplicates.

    Returns:
        Dict with count, percentage, and sample duplicate rows.
    """
    dup_mask = df.duplicated(subset=columns, keep=False)
    dup_count = int(df.duplicated(subset=columns).sum())
    total = len(df)

    return {
        "columns": columns,
        "duplicate_count": dup_count,
        "duplicate_pct": round(dup_count / total * 100, 2) if total > 0 else 0.0,
        "rows_affected": int(dup_mask.sum()),
        "sample": df[df.duplicated(subset=columns, keep="first")]
        .head(5)
        .to_dict(orient="records"),
    }


# --- Pattern: near-duplicates using string similarity ---
def string_similarity(a: str, b: str) -> float:
    """Compute similarity ratio between two strings.

    Args:
        a: First string.
        b: Second string.

    Returns:
        Similarity ratio between 0.0 and 1.0.
    """
    if pd.isna(a) or pd.isna(b):
        return 0.0
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()


def find_near_duplicates(
    df: pd.DataFrame,
    column: str,
    threshold: float = 0.9,
    max_comparisons: int = 10000,
) -> list[dict]:
    """Find near-duplicate strings in a column.

    Args:
        df: DataFrame to analyze.
        column: Column to check for near-duplicates.
        threshold: Minimum similarity ratio to consider as near-duplicate.
        max_comparisons: Limit total pairwise comparisons for performance.

    Returns:
        List of dicts with row_a, row_b, value_a, value_b, similarity.
    """
    values = df[column].dropna().astype(str).tolist()

    # Deduplicate unique values for efficiency
    unique_values = list(set(values))
    near_dupes = []
    comparisons = 0

    for i, val_a in enumerate(unique_values):
        for val_b in unique_values[i + 1 :]:
            comparisons += 1
            if comparisons > max_comparisons:
                return near_dupes

            sim = string_similarity(val_a, val_b)
            if sim >= threshold:
                near_dupes.append(
                    {
                        "value_a": val_a,
                        "value_b": val_b,
                        "similarity": round(sim, 4),
                    }
                )

    return sorted(near_dupes, key=lambda x: x["similarity"], reverse=True)


# --- Pattern: decide which duplicate to keep ---
def dedup_preview(df: pd.DataFrame, keep: str = "first") -> pd.DataFrame:
    """Preview the result of dropping duplicates.

    Args:
        df: DataFrame to deduplicate.
        keep: 'first', 'last', or False (drop all duplicates).

    Returns:
        DataFrame with duplicates removed.
    """
    return df.drop_duplicates(keep=keep)


# --- Pattern: impact analysis ---
def dedup_impact(df: pd.DataFrame) -> dict:
    """Analyze the impact of removing exact duplicates.

    Args:
        df: DataFrame to analyze.

    Returns:
        Dict with before/after row counts and percentage removed.
    """
    before = len(df)
    after = len(df.drop_duplicates())
    removed = before - after

    return {
        "rows_before": before,
        "rows_after": after,
        "rows_removed": removed,
        "pct_removed": round(removed / before * 100, 2) if before > 0 else 0.0,
    }
