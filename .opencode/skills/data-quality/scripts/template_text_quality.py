"""Template: Text-specific quality analysis patterns.

This is a reference template — not a runnable CLI script.
The agent should adapt these patterns when profiling text classification datasets.
"""

import re

import pandas as pd


# --- Pattern: validate text column exists and has correct type ---
def check_text_column(df: pd.DataFrame, text_col: str) -> dict:
    """Validate that the text column exists and contains string data.

    Args:
        df: DataFrame to check.
        text_col: Expected name of the text column.

    Returns:
        Dict with exists, dtype, non_string_count, null_count.
    """
    if text_col not in df.columns:
        return {
            "exists": False,
            "available_columns": list(df.columns),
            "error": f"Column '{text_col}' not found in dataset",
        }

    series = df[text_col]
    non_string = series.dropna().apply(lambda x: not isinstance(x, str)).sum()
    null_count = int(series.isnull().sum())

    return {
        "exists": True,
        "dtype": str(series.dtype),
        "non_string_count": int(non_string),
        "null_count": null_count,
    }


# --- Pattern: text length statistics ---
def text_length_stats(df: pd.DataFrame, text_col: str) -> dict:
    """Compute character and word count distributions for the text column.

    Args:
        df: DataFrame to analyze.
        text_col: Name of the text column.

    Returns:
        Dict with char_length and word_length statistics, plus outlier info.
    """
    if text_col not in df.columns:
        return {"error": f"Column '{text_col}' not found"}

    texts = df[text_col].dropna().astype(str)

    char_lengths = texts.str.len()
    word_lengths = texts.str.split().str.len()

    def _describe(series: pd.Series) -> dict:
        return {
            "min": int(series.min()) if len(series) > 0 else 0,
            "max": int(series.max()) if len(series) > 0 else 0,
            "mean": round(float(series.mean()), 2),
            "median": float(series.median()),
            "std": round(float(series.std()), 2),
            "p5": float(series.quantile(0.05)),
            "p95": float(series.quantile(0.95)),
        }

    empty_count = int((char_lengths == 0).sum())
    short_thresh = 5
    short_count = int((word_lengths < short_thresh).sum())

    return {
        "total_rows": len(texts),
        "char_length": _describe(char_lengths),
        "word_length": _describe(word_lengths),
        "empty_texts": empty_count,
        "empty_pct": round(empty_count / len(texts) * 100, 2)
        if len(texts) > 0
        else 0.0,
        f"short_texts_under_{short_thresh}_words": short_count,
        "short_pct": round(short_count / len(texts) * 100, 2)
        if len(texts) > 0
        else 0.0,
    }


# --- Pattern: detect encoding / mojibake issues ---
def detect_encoding_issues(df: pd.DataFrame, text_col: str) -> dict:
    """Detect encoding problems, non-printable characters, mojibake.

    Args:
        df: DataFrame to analyze.
        text_col: Name of the text column.

    Returns:
        Dict with issue counts and sample problematic rows.
    """
    if text_col not in df.columns:
        return {"error": f"Column '{text_col}' not found"}

    texts = df[text_col].dropna().astype(str)
    total = len(texts)

    # Mojibake: common patterns like Ã© (UTF-8 bytes misread as latin-1)
    mojibake_pattern = re.compile(r"[Ãâ][\x80-\xBF]")
    mojibake_mask = texts.str.contains(mojibake_pattern, na=False)
    mojibake_count = int(mojibake_mask.sum())

    # Non-printable characters (excluding common whitespace: tab, newline, carriage return)
    non_printable_pattern = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
    non_printable_mask = texts.str.contains(non_printable_pattern, na=False)
    non_printable_count = int(non_printable_mask.sum())

    samples = []
    if mojibake_count > 0:
        samples.extend(texts[mojibake_mask].head(3).tolist())
    if non_printable_count > 0:
        samples.extend(texts[non_printable_mask].head(3).tolist())

    return {
        "total_rows": total,
        "mojibake_count": mojibake_count,
        "mojibake_pct": round(mojibake_count / total * 100, 2) if total > 0 else 0.0,
        "non_printable_count": non_printable_count,
        "non_printable_pct": round(non_printable_count / total * 100, 2)
        if total > 0
        else 0.0,
        "sample_issues": samples[:5],
    }


# --- Pattern: language detection (sample-based) ---
def detect_language_sample(
    df: pd.DataFrame, text_col: str, sample_size: int = 100
) -> dict:
    """Sample-based language detection using langdetect.

    Falls back to a simple heuristic if langdetect is not installed.

    Args:
        df: DataFrame to analyze.
        text_col: Name of the text column.
        sample_size: Number of rows to sample for detection.

    Returns:
        Dict with language distribution and mixed_language flag.
    """
    if text_col not in df.columns:
        return {"error": f"Column '{text_col}' not found"}

    texts = df[text_col].dropna().astype(str)
    # Filter very short texts — language detection is unreliable under 20 chars
    texts = texts[texts.str.len() >= 20]

    if len(texts) == 0:
        return {"error": "No texts long enough for language detection"}

    sample_n = min(sample_size, len(texts))
    sample = texts.sample(n=sample_n, random_state=42)

    try:
        from langdetect import LangDetectException, detect

        languages = []
        for text in sample:
            try:
                languages.append(detect(text))
            except LangDetectException:
                languages.append("unknown")

        lang_counts = pd.Series(languages).value_counts().to_dict()
        unique_langs = [k for k in lang_counts if k != "unknown"]

        return {
            "detected": True,
            "method": "langdetect",
            "sample_size": sample_n,
            "language_distribution": {str(k): int(v) for k, v in lang_counts.items()},
            "mixed_language": len(unique_langs) > 1,
            "primary_language": unique_langs[0] if unique_langs else "unknown",
        }
    except ImportError:
        return {
            "detected": False,
            "method": "unavailable",
            "note": "langdetect not installed — pip install langdetect",
        }


# --- Pattern: class imbalance analysis ---
def class_imbalance(df: pd.DataFrame, label_col: str) -> dict:
    """Analyze label distribution and class imbalance.

    Args:
        df: DataFrame to analyze.
        label_col: Name of the label/class column.

    Returns:
        Dict with distribution, imbalance ratio, majority/minority classes.
    """
    if label_col not in df.columns:
        return {"error": f"Column '{label_col}' not found"}

    counts = df[label_col].value_counts()
    total = len(df)

    distribution = {str(k): int(v) for k, v in counts.items()}
    pct_distribution = {str(k): round(v / total * 100, 2) for k, v in counts.items()}

    majority_class = str(counts.index[0])
    minority_class = str(counts.index[-1])
    majority_count = int(counts.iloc[0])
    minority_count = int(counts.iloc[-1])

    imbalance_ratio = (
        round(majority_count / minority_count, 2)
        if minority_count > 0
        else float("inf")
    )

    return {
        "total_rows": total,
        "num_classes": len(counts),
        "distribution": distribution,
        "pct_distribution": pct_distribution,
        "majority_class": majority_class,
        "majority_count": majority_count,
        "majority_pct": pct_distribution[majority_class],
        "minority_class": minority_class,
        "minority_count": minority_count,
        "minority_pct": pct_distribution[minority_class],
        "imbalance_ratio": imbalance_ratio,
        "is_imbalanced": imbalance_ratio > 3.0,
    }


# --- Pattern: find empty or very short texts ---
def find_empty_or_short(
    df: pd.DataFrame, text_col: str, min_length: int = 3
) -> pd.DataFrame:
    """Find rows with empty, NaN, or extremely short text.

    Args:
        df: DataFrame to analyze.
        text_col: Name of the text column.
        min_length: Minimum character length to consider non-empty.

    Returns:
        DataFrame subset with problematic rows (includes original index).
    """
    if text_col not in df.columns:
        return pd.DataFrame()

    mask = df[text_col].isna() | (df[text_col].astype(str).str.len() < min_length)
    return df[mask].copy()
