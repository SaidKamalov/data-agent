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
    """Formalizes the user's data requirements for the pipeline."""

    topic: str
    domain: str
    timeframe: str
    sources_preference: list[str]
    format_preference: str
    size_preference: str
    columns_of_interest: list[str]
    quality_requirements: str
    annotation_task: str
    annotation_labels: list[str]
