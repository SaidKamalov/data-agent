"""Template: Analyzing missing values.

This is a reference template — not a runnable CLI script.
The agent should adapt these patterns when profiling missing data.
"""

import pandas as pd


# --- Pattern: per-column missing count and percentage ---
def missing_summary(df: pd.DataFrame) -> list[dict]:
    """Compute missing value counts and percentages per column.

    Args:
        df: DataFrame to analyze.

    Returns:
        List of dicts with column, missing_count, missing_pct, dtype.
    """
    total_rows = len(df)
    results = []
    for col in df.columns:
        count = int(df[col].isnull().sum())
        results.append(
            {
                "column": col,
                "dtype": str(df[col].dtype),
                "missing_count": count,
                "missing_pct": round(count / total_rows * 100, 2)
                if total_rows > 0
                else 0.0,
            }
        )
    # Sort by missing percentage descending
    return sorted(results, key=lambda x: x["missing_pct"], reverse=True)


# --- Pattern: overall missingness ---
def overall_missing(df: pd.DataFrame) -> dict:
    """Compute dataset-level missingness statistics.

    Args:
        df: DataFrame to analyze.

    Returns:
        Dict with total_cells, total_missing, missing_pct.
    """
    total_cells = df.shape[0] * df.shape[1]
    total_missing = int(df.isnull().sum().sum())
    return {
        "total_cells": total_cells,
        "total_missing": total_missing,
        "missing_pct": round(total_missing / total_cells * 100, 2)
        if total_cells > 0
        else 0.0,
    }


# --- Pattern: identify columns missing together (correlated missingness) ---
def correlated_missing(df: pd.DataFrame, threshold: float = 0.8) -> list[dict]:
    """Find pairs of columns whose missingness is highly correlated.

    Args:
        df: DataFrame to analyze.
        threshold: Minimum absolute correlation to report.

    Returns:
        List of dicts with column_a, column_b, correlation.
    """
    # Create a boolean mask of missingness
    missing_mask = df.isnull().astype(int)

    # Only consider columns that have at least some missing values
    cols_with_missing = [c for c in missing_mask.columns if missing_mask[c].sum() > 0]

    if len(cols_with_missing) < 2:
        return []

    corr_matrix = missing_mask[cols_with_missing].corr()
    pairs = []
    seen = set()

    for i, col_a in enumerate(cols_with_missing):
        for col_b in cols_with_missing[i + 1 :]:
            corr_val = corr_matrix.loc[col_a, col_b]
            pair_key = (col_a, col_b)
            if abs(corr_val) >= threshold and pair_key not in seen:
                pairs.append(
                    {
                        "column_a": col_a,
                        "column_b": col_b,
                        "correlation": round(corr_val, 4),
                    }
                )
                seen.add(pair_key)

    return sorted(pairs, key=lambda x: abs(x["correlation"]), reverse=True)


# --- Pattern: compare rows with vs without missing values in a column ---
def compare_missing_vs_present(df: pd.DataFrame, column: str) -> dict:
    """Compare descriptive statistics between rows where column is missing vs present.

    Useful for detecting MNAR (missing not at random) patterns.

    Args:
        df: DataFrame to analyze.
        column: Column to split on.

    Returns:
        Dict with 'missing' and 'present' sub-dicts of describe() output.
    """
    missing_rows = df[df[column].isnull()]
    present_rows = df[df[column].notnull()]

    return {
        "missing_count": len(missing_rows),
        "present_count": len(present_rows),
        "missing_describe": missing_rows.describe(include="all").to_dict()
        if len(missing_rows) > 0
        else {},
        "present_describe": present_rows.describe(include="all").to_dict()
        if len(present_rows) > 0
        else {},
    }


# --- Pattern: row-level missingness ---
def row_missing_distribution(df: pd.DataFrame) -> dict:
    """Analyze how many columns are missing per row.

    Args:
        df: DataFrame to analyze.

    Returns:
        Dict with distribution of missing columns per row.
    """
    missing_per_row = df.isnull().sum(axis=1)
    return {
        "min_missing": int(missing_per_row.min()),
        "max_missing": int(missing_per_row.max()),
        "mean_missing": round(float(missing_per_row.mean()), 2),
        "median_missing": float(missing_per_row.median()),
        "rows_fully_complete": int((missing_per_row == 0).sum()),
        "rows_any_missing": int((missing_per_row > 0).sum()),
        "pct_rows_any_missing": round(float((missing_per_row > 0).mean()) * 100, 2),
    }


# --- Pattern: classify columns by missingness type heuristic ---
def classify_missingness(df: pd.DataFrame, column: str) -> str:
    """Heuristic classification of missingness type for a column.

    This is a simplified heuristic — real analysis requires domain knowledge.

    Args:
        df: DataFrame to analyze.
        column: Column to classify.

    Returns:
        One of 'MCAR', 'MAR', 'MNAR', or 'likely_structural'.
    """
    missing_pct = df[column].isnull().mean()

    if missing_pct == 0:
        return "none"

    # Check if missingness correlates with other columns
    other_cols = [c for c in df.columns if c != column]
    strong_correlations = 0

    for other_col in other_cols:
        if df[other_col].dtype in ["object", "category", "bool"]:
            continue
        try:
            corr = (
                df[column]
                .isnull()
                .astype(int)
                .corr(df[other_col].fillna(df[other_col].median()))
            )
            if abs(corr) > 0.3:
                strong_correlations += 1
        except (TypeError, ValueError):
            continue

    if strong_correlations >= 2:
        return "MAR"
    if missing_pct > 0.5:
        return "likely_structural"
    if strong_correlations == 0:
        return "MCAR"
    return "MNAR"
