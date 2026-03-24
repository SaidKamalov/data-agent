"""Template: Imputing missing values.

This is a reference template — not a runnable CLI script.
The agent should adapt these patterns when applying data cleaning.
"""

import pandas as pd
from sklearn.impute import SimpleImputer


# --- Pattern: drop rows with missing values ---
def drop_missing_rows(
    df: pd.DataFrame, columns: list[str] | None = None, thresh: float | None = None
) -> pd.DataFrame:
    """Drop rows with missing values.

    Args:
        df: DataFrame to clean.
        columns: Subset of columns to check, or None for all.
        thresh: Require at least this many non-NA values to keep a row.

    Returns:
        DataFrame with rows dropped.
    """
    if thresh is not None:
        return df.dropna(thresh=int(thresh * len(df.columns)))
    return df.dropna(subset=columns)


# --- Pattern: mean/median/mode imputation ---
def impute_statistical(
    df: pd.DataFrame,
    column: str,
    strategy: str = "median",
) -> pd.DataFrame:
    """Impute missing values using a statistical strategy.

    Args:
        df: DataFrame to clean.
        column: Column to impute.
        strategy: 'mean', 'median', or 'most_frequent'.

    Returns:
        DataFrame with imputed values.
    """
    df = df.copy()
    if strategy == "mean":
        df[column] = df[column].fillna(df[column].mean())
    elif strategy == "median":
        df[column] = df[column].fillna(df[column].median())
    elif strategy == "most_frequent":
        mode_val = df[column].mode()
        if len(mode_val) > 0:
            df[column] = df[column].fillna(mode_val.iloc[0])
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    return df


# --- Pattern: forward/backward fill ---
def impute_fill(
    df: pd.DataFrame,
    column: str,
    method: str = "ffill",
    limit: int | None = None,
) -> pd.DataFrame:
    """Impute missing values using forward or backward fill.

    Args:
        df: DataFrame to clean.
        column: Column to impute.
        method: 'ffill' or 'bfill'.
        limit: Maximum consecutive NaN values to fill.

    Returns:
        DataFrame with imputed values.
    """
    df = df.copy()
    if method == "ffill":
        df[column] = df[column].ffill(limit=limit)
    elif method == "bfill":
        df[column] = df[column].bfill(limit=limit)
    else:
        raise ValueError(f"Unknown method: {method}")
    return df


# --- Pattern: constant fill ---
def impute_constant(
    df: pd.DataFrame,
    column: str,
    value: str | int | float,
) -> pd.DataFrame:
    """Impute missing values with a constant.

    Args:
        df: DataFrame to clean.
        column: Column to impute.
        value: Constant to fill with.

    Returns:
        DataFrame with imputed values.
    """
    df = df.copy()
    df[column] = df[column].fillna(value)
    return df


# --- Pattern: sklearn SimpleImputer for multiple columns ---
def impute_multi_column(
    df: pd.DataFrame,
    columns: list[str],
    strategy: str = "median",
) -> pd.DataFrame:
    """Impute multiple columns using sklearn SimpleImputer.

    Args:
        df: DataFrame to clean.
        columns: Columns to impute.
        strategy: 'mean', 'median', 'most_frequent', or 'constant'.

    Returns:
        DataFrame with imputed values.
    """
    df = df.copy()
    imputer = SimpleImputer(strategy=strategy)
    df[columns] = imputer.fit_transform(df[columns])
    return df


# --- Pattern: distribution preservation check ---
def imputation_impact(
    df: pd.DataFrame,
    column: str,
    strategy: str = "median",
) -> dict:
    """Compare distribution before and after imputation.

    Args:
        df: DataFrame to analyze.
        column: Column to impute and compare.
        strategy: Imputation strategy.

    Returns:
        Dict with before/after statistics and missing count filled.
    """
    original = df[column].dropna()
    filled = impute_statistical(df, column, strategy)[column]

    missing_count = int(df[column].isnull().sum())

    return {
        "column": column,
        "strategy": strategy,
        "missing_filled": missing_count,
        "before": {
            "count": int(len(original)),
            "mean": round(float(original.mean()), 4),
            "std": round(float(original.std()), 4),
            "min": float(original.min()),
            "25%": float(original.quantile(0.25)),
            "50%": float(original.median()),
            "75%": float(original.quantile(0.75)),
            "max": float(original.max()),
            "skew": round(float(original.skew()), 4),
        },
        "after": {
            "count": int(len(filled)),
            "mean": round(float(filled.mean()), 4),
            "std": round(float(filled.std()), 4),
            "min": float(filled.min()),
            "25%": float(filled.quantile(0.25)),
            "50%": float(filled.median()),
            "75%": float(filled.quantile(0.75)),
            "max": float(filled.max()),
            "skew": round(float(filled.skew()), 4),
        },
    }
