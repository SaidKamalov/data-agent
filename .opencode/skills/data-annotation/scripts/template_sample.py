"""Template: Sampling patterns for data annotation.

This is a reference template — not a runnable CLI script.
The agent should adapt these patterns when sampling datasets for labeling.
"""

import pandas as pd


# --- Pattern: random sampling ---
def sample_random(df: pd.DataFrame, n: int, seed: int = 42) -> pd.DataFrame:
    """Draw n random rows from the DataFrame.

    Args:
        df: Source DataFrame.
        n: Number of rows to sample.
        seed: Random seed for reproducibility.

    Returns:
        Sampled DataFrame with original indices preserved.
    """
    n = min(n, len(df))
    sample = df.sample(n=n, random_state=seed)
    return sample


# --- Pattern: stratified sampling (proportional) ---
def sample_stratified(
    df: pd.DataFrame,
    label_col: str,
    n: int,
    seed: int = 42,
) -> pd.DataFrame:
    """Draw n rows with stratification by label column.

    Distributes samples proportionally across label groups.
    Falls back to random sampling if label_col is missing.

    Args:
        df: Source DataFrame.
        label_col: Column name to stratify by.
        n: Total number of rows to sample.
        seed: Random seed for reproducibility.

    Returns:
        Sampled DataFrame with original indices preserved.
    """
    if label_col not in df.columns:
        return sample_random(df, n, seed)

    # Calculate per-stratum sample sizes proportional to group size
    group_sizes = df.groupby(label_col).size()
    total = len(df)
    stratum_samples = {}

    for label, size in group_sizes.items():
        proportion = size / total
        stratum_n = max(1, round(n * proportion))
        stratum_samples[label] = min(stratum_n, size)

    # Adjust to hit exact target n
    current_total = sum(stratum_samples.values())
    diff = n - current_total
    if diff != 0:
        largest = max(stratum_samples, key=stratum_samples.get)
        stratum_samples[largest] = max(
            1, min(stratum_samples[largest] + diff, group_sizes[largest])
        )

    # Sample from each stratum
    parts = []
    for label, stratum_n in stratum_samples.items():
        group = df[df[label_col] == label]
        parts.append(group.sample(n=stratum_n, random_state=seed))

    return pd.concat(parts).sort_index()


# --- Pattern: stratified sampling (balanced) ---
def sample_balanced(
    df: pd.DataFrame,
    label_col: str,
    n: int,
    seed: int = 42,
) -> pd.DataFrame:
    """Draw n rows with equal representation across label groups.

    Useful when target classes are imbalanced and you want
    equal coverage for annotation.

    Args:
        df: Source DataFrame.
        label_col: Column name to stratify by.
        n: Total number of rows to sample.
        seed: Random seed for reproducibility.

    Returns:
        Sampled DataFrame with original indices preserved.
    """
    if label_col not in df.columns:
        return sample_random(df, n, seed)

    groups = df.groupby(label_col)
    n_classes = len(groups)
    per_class = n // n_classes

    parts = []
    for label, group in groups:
        take = min(per_class, len(group))
        parts.append(group.sample(n=take, random_state=seed))

    return pd.concat(parts).sort_index()


# --- Pattern: find label column heuristically ---
def find_label_column(df: pd.DataFrame) -> str | None:
    """Try to find a label/class column in the DataFrame.

    Looks for common naming patterns and low-cardinality columns.

    Args:
        df: DataFrame to inspect.

    Returns:
        Column name if found, None otherwise.
    """
    candidates = ["label", "class", "category", "target", "sentiment", "type"]
    for col in df.columns:
        if col.lower() in candidates:
            return col
        # Heuristic: low-cardinality string column
        if df[col].dtype == "object" and df[col].nunique() <= 20:
            return col
    return None


# --- Pattern: preserve original indices ---
def sample_with_index(
    df: pd.DataFrame,
    n: int,
    label_col: str | None = None,
    seed: int = 42,
) -> pd.DataFrame:
    """Sample rows and ensure original DataFrame index is preserved.

    The index column is useful for traceability — linking labeled
    samples back to the original dataset.

    Args:
        df: Source DataFrame.
        n: Number of rows to sample.
        label_col: Optional column for stratified sampling.
        seed: Random seed for reproducibility.

    Returns:
        Sampled DataFrame with 'original_index' column added.
    """
    if label_col and label_col in df.columns:
        sampled = sample_stratified(df, label_col, n, seed)
    else:
        sampled = sample_random(df, n, seed)

    sampled = sampled.copy()
    sampled["original_index"] = sampled.index
    return sampled


# --- Pattern: calculate sample statistics ---
def sample_stats(
    df: pd.DataFrame, sample: pd.DataFrame, label_col: str | None = None
) -> dict:
    """Compare sample distribution to full dataset.

    Args:
        df: Full DataFrame.
        sample: Sampled DataFrame.
        label_col: Optional label column for distribution comparison.

    Returns:
        Dict with sampling statistics.
    """
    stats: dict = {
        "total_rows": len(df),
        "sampled_rows": len(sample),
        "sample_pct": round(len(sample) / len(df) * 100, 2),
    }

    if label_col and label_col in df.columns:
        full_dist = df[label_col].value_counts(normalize=True).to_dict()
        sample_dist = sample[label_col].value_counts(normalize=True).to_dict()
        stats["full_distribution"] = full_dist
        stats["sample_distribution"] = sample_dist

    return stats
