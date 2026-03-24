"""Template: Detecting outliers with IQR and z-score.

This is a reference template — not a runnable CLI script.
The agent should adapt these patterns when detecting outliers.
"""

import pandas as pd
import numpy as np
from scipy import stats


# --- Pattern: IQR-based outlier detection ---
def iqr_bounds(series: pd.Series, multiplier: float = 1.5) -> tuple[float, float]:
    """Compute IQR-based outlier bounds.

    Args:
        series: Numeric series to analyze.
        multiplier: IQR multiplier (1.5 is standard, 3.0 for extreme outliers).

    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    return float(lower), float(upper)


def detect_outliers_iqr(
    df: pd.DataFrame, columns: list[str] | None = None, multiplier: float = 1.5
) -> list[dict]:
    """Detect outliers using the IQR method for numeric columns.

    Args:
        df: DataFrame to analyze.
        columns: Specific columns to check, or None for all numeric columns.
        multiplier: IQR multiplier.

    Returns:
        List of dicts with column, outlier_count, outlier_pct, bounds, and statistics.
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()

    results = []
    for col in columns:
        series = df[col].dropna()
        if len(series) == 0:
            continue

        lower, upper = iqr_bounds(series, multiplier)
        outlier_mask = (series < lower) | (series > upper)
        outlier_count = int(outlier_mask.sum())

        results.append(
            {
                "column": col,
                "outlier_count": outlier_count,
                "outlier_pct": round(outlier_count / len(series) * 100, 2),
                "lower_bound": lower,
                "upper_bound": upper,
                "q1": float(series.quantile(0.25)),
                "q3": float(series.quantile(0.75)),
                "iqr": float(series.quantile(0.75) - series.quantile(0.25)),
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": round(float(series.mean()), 4),
                "std": round(float(series.std()), 4),
            }
        )

    return sorted(results, key=lambda x: x["outlier_count"], reverse=True)


# --- Pattern: z-score-based outlier detection ---
def detect_outliers_zscore(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    threshold: float = 3.0,
) -> list[dict]:
    """Detect outliers using z-score method.

    Args:
        df: DataFrame to analyze.
        columns: Specific columns to check, or None for all numeric columns.
        threshold: Z-score threshold (3.0 is standard).

    Returns:
        List of dicts with column, outlier_count, outlier_pct, and threshold.
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()

    results = []
    for col in columns:
        series = df[col].dropna()
        if len(series) == 0 or series.std() == 0:
            continue

        z_scores = np.abs(stats.zscore(series, nan_policy="omit"))
        outlier_mask = z_scores > threshold
        outlier_count = int(outlier_mask.sum())

        results.append(
            {
                "column": col,
                "method": "zscore",
                "threshold": threshold,
                "outlier_count": outlier_count,
                "outlier_pct": round(outlier_count / len(series) * 100, 2),
            }
        )

    return sorted(results, key=lambda x: x["outlier_count"], reverse=True)


# --- Pattern: distribution impact analysis ---
def distribution_comparison(
    df: pd.DataFrame, column: str, multiplier: float = 1.5
) -> dict:
    """Compare distributions with and without outliers.

    Args:
        df: DataFrame to analyze.
        column: Column to compare.
        multiplier: IQR multiplier for outlier bounds.

    Returns:
        Dict with before/after describe() output and rows removed.
    """
    series = df[column].dropna()
    lower, upper = iqr_bounds(series, multiplier)
    inliers = series[(series >= lower) & (series <= upper)]

    return {
        "column": column,
        "before": {
            "count": int(len(series)),
            "mean": round(float(series.mean()), 4),
            "std": round(float(series.std()), 4),
            "min": float(series.min()),
            "25%": float(series.quantile(0.25)),
            "50%": float(series.median()),
            "75%": float(series.quantile(0.75)),
            "max": float(series.max()),
        },
        "after": {
            "count": int(len(inliers)),
            "mean": round(float(inliers.mean()), 4),
            "std": round(float(inliers.std()), 4),
            "min": float(inliers.min()),
            "25%": float(inliers.quantile(0.25)),
            "50%": float(inliers.median()),
            "75%": float(inliers.quantile(0.75)),
            "max": float(inliers.max()),
        },
        "rows_removed": int(len(series) - len(inliers)),
        "pct_removed": round((len(series) - len(inliers)) / len(series) * 100, 2)
        if len(series) > 0
        else 0.0,
    }


# --- Pattern: list actual outlier values ---
def list_outliers(
    df: pd.DataFrame, column: str, multiplier: float = 1.5, max_rows: int = 50
) -> list[dict]:
    """List outlier rows for a specific column.

    Args:
        df: DataFrame to analyze.
        column: Column to check.
        multiplier: IQR multiplier.
        max_rows: Maximum rows to return.

    Returns:
        List of dicts representing outlier rows.
    """
    series = df[column]
    lower, upper = iqr_bounds(series.dropna(), multiplier)
    outlier_mask = (series < lower) | (series > upper)
    return df[outlier_mask].head(max_rows).to_dict(orient="records")
