"""Pydantic data models for the DataAgent pipeline."""

from pydantic import BaseModel


class DatasetOption(BaseModel):
    """Represents a discovered dataset from any source."""

    name: str
    description: str
    source: str  # "kaggle" | "huggingface" | "web"
    size: str | None = None
    format: str | None = None
    url: str
    download_id: str  # kaggle slug or HF dataset id


class DataContract(BaseModel):
    """Formalizes the user's data requirements for the text classification pipeline.

    Currently only 'classification' is supported as annotation_task.
    """

    topic: str
    domain: str
    timeframe: str
    sources_preference: list[str]
    format_preference: str
    size_preference: str
    text_column: str
    columns_of_interest: list[str]
    quality_requirements: str
    annotation_task: str = "classification"
    annotation_labels: list[str]
    al_strategy: str = "entropy"  # entropy | margin | random
    al_val_split: float = 0.2
