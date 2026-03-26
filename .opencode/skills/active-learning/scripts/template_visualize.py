"""Template: Visualize active learning results with matplotlib.

This is a reference template — not a runnable CLI script.
The agent should adapt these patterns when generating learning curve
visualizations for active learning evaluation.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd


# --- Pattern: save figure ---
def save_figure(fig: plt.Figure, path: str, dpi: int = 150) -> None:
    """Save a matplotlib figure with tight layout.

    Args:
        fig: Matplotlib Figure object.
        path: Output file path.
        dpi: Resolution in dots per inch.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


# --- Pattern: accuracy + F1 vs iteration ---
def plot_learning_curve(
    iterations_df: pd.DataFrame,
    save_path: str | None = None,
) -> plt.Figure:
    """Plot accuracy and F1 scores vs iteration number.

    Args:
        iterations_df: DataFrame with columns: iteration, accuracy, f1_macro.
        save_path: If provided, save figure to this path.

    Returns:
        matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(
        iterations_df["iteration"],
        iterations_df["accuracy"],
        marker="o",
        linewidth=2,
        label="Accuracy",
    )
    ax.plot(
        iterations_df["iteration"],
        iterations_df["f1_macro"],
        marker="s",
        linewidth=2,
        label="F1 (macro)",
    )

    ax.set_xlabel("Iteration", fontsize=12)
    ax.set_ylabel("Score", fontsize=12)
    ax.set_title("Active Learning: Performance per Iteration", fontsize=14)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(iterations_df["iteration"].tolist())

    fig.tight_layout()

    if save_path:
        save_figure(fig, save_path)

    return fig


# --- Pattern: accuracy + F1 vs labeled set size ---
def plot_train_size_curve(
    iterations_df: pd.DataFrame,
    save_path: str | None = None,
) -> plt.Figure:
    """Plot accuracy and F1 vs labeled set size (canonical AL learning curve).

    Args:
        iterations_df: DataFrame with columns: train_size, accuracy, f1_macro.
        save_path: If provided, save figure to this path.

    Returns:
        matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(
        iterations_df["train_size"],
        iterations_df["accuracy"],
        marker="o",
        linewidth=2,
        label="Accuracy",
    )
    ax.plot(
        iterations_df["train_size"],
        iterations_df["f1_macro"],
        marker="s",
        linewidth=2,
        label="F1 (macro)",
    )

    ax.set_xlabel("Labeled Set Size", fontsize=12)
    ax.set_ylabel("Score", fontsize=12)
    ax.set_title("Active Learning: Performance vs Labeled Set Size", fontsize=14)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()

    if save_path:
        save_figure(fig, save_path)

    return fig


# --- Pattern: baseline vs AL comparison bar chart ---
def plot_baseline_comparison(
    baseline_metrics: dict,
    al_metrics: dict,
    save_path: str | None = None,
) -> plt.Figure:
    """Side-by-side bar chart comparing baseline vs active learning final.

    Args:
        baseline_metrics: Dict with 'accuracy' and 'f1_macro'.
        al_metrics: Dict with 'accuracy' and 'f1_macro'.
        save_path: If provided, save figure to this path.

    Returns:
        matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    metrics = ["accuracy", "f1_macro"]
    baseline_vals = [baseline_metrics.get(m, 0) for m in metrics]
    al_vals = [al_metrics.get(m, 0) for m in metrics]

    x = range(len(metrics))
    width = 0.35

    bars1 = ax.bar(
        [i - width / 2 for i in x],
        baseline_vals,
        width,
        label="Baseline",
        color="#4A90D9",
    )
    bars2 = ax.bar(
        [i + width / 2 for i in x],
        al_vals,
        width,
        label="Active Learning",
        color="#E8685A",
    )

    ax.set_ylabel("Score", fontsize=12)
    ax.set_title("Baseline vs Active Learning", fontsize=14)
    ax.set_xticks(list(x))
    ax.set_xticklabels(["Accuracy", "F1 (macro)"], fontsize=11)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 1.15)
    ax.grid(True, alpha=0.3, axis="y")

    # Add value labels on bars
    for bar_group in [bars1, bars2]:
        for bar in bar_group:
            height = bar.get_height()
            ax.annotate(
                f"{height:.2f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10,
            )

    fig.tight_layout()

    if save_path:
        save_figure(fig, save_path)

    return fig
