"""Template: Compute uncertainty scores and select samples for active learning.

This is a reference template — not a runnable CLI script.
The agent should adapt these patterns when computing uncertainty scores
for sample selection in active learning.
"""

import numpy as np


# --- Pattern: entropy-based uncertainty ---
def entropy_scores(probabilities: np.ndarray) -> np.ndarray:
    """Compute Shannon entropy for each sample's predicted probabilities.

    High entropy = high uncertainty (model is confused).

    Args:
        probabilities: Array of shape (n_samples, n_classes) with class probabilities.

    Returns:
        Array of shape (n_samples,) with entropy scores.
    """
    eps = 1e-10  # avoid log(0)
    return -np.sum(probabilities * np.log(probabilities + eps), axis=1)


# --- Pattern: margin-based uncertainty ---
def margin_scores(probabilities: np.ndarray) -> np.ndarray:
    """Compute margin between top two predicted probabilities.

    Low margin = high uncertainty (top two classes are close).

    Args:
        probabilities: Array of shape (n_samples, n_classes) with class probabilities.

    Returns:
        Array of shape (n_samples,) with margin scores (higher = more uncertain).
    """
    sorted_probs = np.sort(probabilities, axis=1)
    margin = sorted_probs[:, -1] - sorted_probs[:, -2]
    # Invert so higher = more uncertain
    return 1.0 - margin


# --- Pattern: least confidence uncertainty ---
def least_confidence_scores(probabilities: np.ndarray) -> np.ndarray:
    """Compute least confidence score for each sample.

    Low max probability = high uncertainty.

    Args:
        probabilities: Array of shape (n_samples, n_classes) with class probabilities.

    Returns:
        Array of shape (n_samples,) with least confidence scores (higher = more uncertain).
    """
    return 1.0 - np.max(probabilities, axis=1)


# --- Pattern: dispatch to strategy ---
def compute_uncertainty(
    probabilities: np.ndarray,
    strategy: str = "entropy",
) -> np.ndarray:
    """Compute uncertainty scores using the specified strategy.

    Args:
        probabilities: Array of shape (n_samples, n_classes).
        strategy: One of 'entropy', 'margin', or 'least_confidence'.

    Returns:
        Array of shape (n_samples,) with uncertainty scores.
    """
    strategies = {
        "entropy": entropy_scores,
        "margin": margin_scores,
        "least_confidence": least_confidence_scores,
    }
    fn = strategies.get(strategy)
    if fn is None:
        raise ValueError(
            f"Unknown strategy: {strategy}. Use: {list(strategies.keys())}"
        )
    return fn(probabilities)


# --- Pattern: select top-k uncertain samples ---
def select_top_k(
    scores: np.ndarray,
    pool_indices: np.ndarray,
    k: int,
) -> np.ndarray:
    """Select the top-k samples with highest uncertainty.

    Args:
        scores: Array of uncertainty scores (one per pool sample).
        pool_indices: Array of original indices corresponding to scores.
        k: Number of samples to select.

    Returns:
        Array of original indices for the selected samples.
    """
    k = min(k, len(scores))
    top_k_positions = np.argsort(scores)[-k:][::-1]
    return pool_indices[top_k_positions]


# --- Pattern: random selection baseline ---
def select_random(
    pool_indices: np.ndarray,
    k: int,
    seed: int = 42,
) -> np.ndarray:
    """Select k random samples from the pool.

    Args:
        pool_indices: Array of original indices for the pool.
        k: Number of samples to select.
        seed: Random seed for reproducibility.

    Returns:
        Array of original indices for the selected samples.
    """
    rng = np.random.RandomState(seed)
    k = min(k, len(pool_indices))
    selected_positions = rng.choice(len(pool_indices), size=k, replace=False)
    return pool_indices[selected_positions]
