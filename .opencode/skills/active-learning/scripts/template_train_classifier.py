"""Template: Train a TF-IDF + Logistic Regression classifier.

This is a reference template — not a runnable CLI script.
The agent should adapt these patterns when training classifiers for active learning.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
)
from sklearn.pipeline import Pipeline


# --- Pattern: build TF-IDF + LogReg pipeline ---
def build_tfidf_pipeline(
    max_features: int = 5000,
    ngram_range: tuple[int, int] = (1, 2),
    C: float = 1.0,
    max_iter: int = 1000,
) -> Pipeline:
    """Build a sklearn Pipeline with TfidfVectorizer and LogisticRegression.

    Args:
        max_features: Maximum number of TF-IDF features.
        ngram_range: N-gram range for TF-IDF.
        C: Inverse regularization strength for LogisticRegression.
        max_iter: Maximum iterations for LogisticRegression solver.

    Returns:
        An un-fitted sklearn Pipeline.
    """
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=max_features,
                    ngram_range=ngram_range,
                    sublinear_tf=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    C=C,
                    max_iter=max_iter,
                    random_state=42,
                ),
            ),
        ]
    )


# --- Pattern: train classifier ---
def train_classifier(
    X_train: list[str] | np.ndarray,
    y_train: list[str] | np.ndarray,
    pipeline: Pipeline | None = None,
) -> Pipeline:
    """Fit a TF-IDF + LogReg pipeline on training data.

    Args:
        X_train: Training text samples.
        y_train: Training labels.
        pipeline: Optional pre-built pipeline. If None, uses default.

    Returns:
        Fitted sklearn Pipeline.
    """
    if pipeline is None:
        pipeline = build_tfidf_pipeline()
    pipeline.fit(X_train, y_train)
    return pipeline


# --- Pattern: evaluate classifier ---
def evaluate_classifier(
    model: Pipeline,
    X_test: list[str] | np.ndarray,
    y_test: list[str] | np.ndarray,
    labels: list[str] | None = None,
) -> dict:
    """Evaluate a trained classifier on test data.

    Args:
        model: Fitted sklearn Pipeline.
        X_test: Test text samples.
        y_test: Test labels.
        labels: Optional ordered list of label names.

    Returns:
        Dict with accuracy, f1_macro, f1_weighted, and per-class metrics.
    """
    y_pred = model.predict(X_test)

    report = classification_report(
        y_test,
        y_pred,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )

    return {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "f1_macro": round(
            f1_score(y_test, y_pred, average="macro", zero_division=0), 4
        ),
        "f1_weighted": round(
            f1_score(y_test, y_pred, average="weighted", zero_division=0), 4
        ),
        "per_class": {
            cls: {
                "precision": round(metrics["precision"], 4),
                "recall": round(metrics["recall"], 4),
                "f1": round(metrics["f1-score"], 4),
                "support": int(metrics["support"]),
            }
            for cls, metrics in report.items()
            if cls not in ("accuracy", "macro avg", "weighted avg")
        },
    }


# --- Pattern: predict class probabilities ---
def predict_proba(
    model: Pipeline,
    X: list[str] | np.ndarray,
) -> np.ndarray:
    """Predict class probabilities for a set of samples.

    Args:
        model: Fitted sklearn Pipeline.
        X: Text samples to predict on.

    Returns:
        Numpy array of shape (n_samples, n_classes) with class probabilities.
    """
    return model.predict_proba(X)


# --- Pattern: encode string labels to integers ---
def encode_labels(
    y: list[str] | np.ndarray,
    label_list: list[str] | None = None,
) -> tuple[np.ndarray, dict[str, int]]:
    """Convert string labels to integer encoding.

    Args:
        y: Array of string labels.
        label_list: Ordered list of label names. If None, sorted unique values.

    Returns:
        Tuple of (encoded_array, label_to_index_mapping).
    """
    if label_list is None:
        label_list = sorted(set(y))
    mapping = {label: idx for idx, label in enumerate(label_list)}
    encoded = np.array([mapping[label] for label in y])
    return encoded, mapping
