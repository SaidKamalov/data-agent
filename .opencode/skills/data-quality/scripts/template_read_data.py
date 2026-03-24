"""Template: Reading data into pandas.

This is a reference template — not a runnable CLI script.
The agent should adapt these patterns when loading datasets for quality analysis.
"""

import pandas as pd
from pathlib import Path


# --- Pattern: detect file format from extension ---
def detect_format(file_path: str) -> str:
    """Detect file format from extension.

    Args:
        file_path: Path to the data file.

    Returns:
        One of 'csv', 'parquet', 'excel', 'json', or 'unknown'.
    """
    ext = Path(file_path).suffix.lower()
    mapping = {
        ".csv": "csv",
        ".tsv": "csv",
        ".parquet": "parquet",
        ".pq": "parquet",
        ".xlsx": "excel",
        ".xls": "excel",
        ".json": "json",
        ".jsonl": "json",
    }
    return mapping.get(ext, "unknown")


# --- Pattern: read CSV with encoding fallback ---
def read_csv_safe(file_path: str) -> pd.DataFrame:
    """Try multiple encodings and delimiters to read a CSV.

    Args:
        file_path: Path to the CSV file.

    Returns:
        Loaded DataFrame.

    Raises:
        ValueError: If no encoding/delimiter combination works.
    """
    encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
    delimiters = [",", ";", "\t", "|"]

    for encoding in encodings:
        for delimiter in delimiters:
            try:
                df = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    sep=delimiter,
                    on_bad_lines="warn",
                    low_memory=False,
                )
                # Heuristic: a valid parse produces more than 1 column
                if df.shape[1] > 1:
                    return df
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue

    raise ValueError(f"Could not read {file_path} with any encoding/delimiter combo")


# --- Pattern: read Parquet ---
def read_parquet_safe(file_path: str, columns: list[str] | None = None) -> pd.DataFrame:
    """Read a Parquet file, optionally selecting specific columns.

    Args:
        file_path: Path to the Parquet file.
        columns: Optional list of columns to load.

    Returns:
        Loaded DataFrame.
    """
    return pd.read_parquet(file_path, columns=columns)


# --- Pattern: read Excel (single or multi-sheet) ---
def read_excel_safe(
    file_path: str, sheet_name: str | int | None = 0
) -> pd.DataFrame | dict[str, pd.DataFrame]:
    """Read an Excel file.

    Args:
        file_path: Path to the Excel file.
        sheet_name: Sheet name/index, or None to read all sheets.

    Returns:
        DataFrame if single sheet, dict of DataFrames if all sheets.
    """
    return pd.read_excel(file_path, sheet_name=sheet_name)


# --- Pattern: read JSON ---
def read_json_safe(file_path: str) -> pd.DataFrame:
    """Read a JSON or JSONL file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Loaded DataFrame.
    """
    path = Path(file_path)
    if path.suffix == ".jsonl":
        return pd.read_json(file_path, lines=True)
    return pd.read_json(file_path)


# --- Pattern: auto-detect and load ---
def read_auto(file_path: str) -> pd.DataFrame:
    """Auto-detect format and load data.

    Args:
        file_path: Path to the data file.

    Returns:
        Loaded DataFrame.

    Raises:
        ValueError: If format is unsupported.
    """
    fmt = detect_format(file_path)
    readers = {
        "csv": read_csv_safe,
        "parquet": read_parquet_safe,
        "excel": read_excel_safe,
        "json": read_json_safe,
    }
    reader = readers.get(fmt)
    if reader is None:
        raise ValueError(f"Unsupported file format: {fmt}")
    return reader(file_path)


# --- Pattern: initial inspection ---
def inspect(df: pd.DataFrame) -> dict:
    """Generate a quick profile of the DataFrame.

    Args:
        df: DataFrame to inspect.

    Returns:
        Dict with shape, dtypes, head, and info summary.
    """
    return {
        "shape": list(df.shape),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "head": df.head(5).to_dict(orient="records"),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1_048_576, 2),
    }
