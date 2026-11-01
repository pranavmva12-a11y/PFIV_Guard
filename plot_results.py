from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent

RESULTS_DIR = BASE_DIR / "results"
PLOT_DIR = RESULTS_DIR / "plots"

PLOT_DIR.mkdir(parents=True, exist_ok=True)


def load_results():
    path = RESULTS_DIR / "model_comparison.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"Results file not found: {path}"
        )

    return pd.read_csv(path)


def plot_model_metrics(df):
    metrics = [
        "Accuracy",
        "Precision",
        "Recall",
        "F1"
    ]

    x = np.arange(len(df))
    width = 0.18

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, metric in enumerate(metrics):
        values = df[metric] * 100

        ax.bar(
            x + (i - 1.5) * width,
            values,
            width,
            label=metric
        )

    ax.set_xticks(x)
    ax.set_xticklabels(df["Model"])
    ax.set_ylabel("Score (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Model Performance Comparison")
    ax.legend()

    for i, metric in enumerate(metrics):
        values = df[metric] * 100

        for j, value in enumerate(values):
            ax.text(
                x[j] + (i - 1.5) * width,
                value + 1,
                f"{value:.2f}",
                ha="center",
                fontsize=8
            )

    plt.tight_layout()

    plt.savefig(
        PLOT_DIR / "model_metrics_comparison.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


def plot_accuracy(df):
    fig, ax = plt.subplots(figsize=(8, 5))

    values = df["Accuracy"] * 100

    bars = ax.bar(
        df["Model"],
        values
    )

    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Accuracy Comparison")

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 1,
            f"{value:.2f}%",
            ha="center"
        )

    plt.tight_layout()

    plt.savefig(
        PLOT_DIR / "accuracy_comparison.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


def plot_confusion_matrix(matrix, title, filename):
    fig, ax = plt.subplots(figsize=(6, 5))

    ax.imshow(matrix)

    ax.set_title(title)
    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("Actual Label")

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])

    ax.set_xticklabels([
        "Legitimate",
        "Phishing"
    ])

    ax.set_yticklabels([
        "Legitimate",
        "Phishing"
    ])

    for i in range(2):
        for j in range(2):
            ax.text(
                j,
                i,
                str(matrix[i, j]),
                ha="center",
                va="center",
                fontsize=14
            )

    plt.tight_layout()

    plt.savefig(
        PLOT_DIR / filename,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


def plot_training_time(df):
    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(
        df["Model"],
        df["Training_Time_sec"]
    )

    ax.set_ylabel("Training Time (seconds)")
    ax.set_title("Training Time Comparison")

    for bar, value in zip(
        bars,
        df["Training_Time_sec"]
    ):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.01,
            f"{value:.3f}",
            ha="center"
        )

    plt.tight_layout()

    plt.savefig(
        PLOT_DIR / "training_time_comparison.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


def create_summary(df):
    summary = df.copy()

    summary["Accuracy (%)"] = (
        summary["Accuracy"] * 100
    ).round(2)

    summary["Precision (%)"] = (
        summary["Precision"] * 100
    ).round(2)

    summary["Recall (%)"] = (
        summary["Recall"] * 100
    ).round(2)

    summary["F1 (%)"] = (
        summary["F1"] * 100
    ).round(2)

    summary = summary[
        [
            "Model",
            "Accuracy (%)",
            "Precision (%)",
            "Recall (%)",
            "F1 (%)",
            "Training_Time_sec"
        ]
    ]

    summary.to_csv(
        RESULTS_DIR / "final_results_table.csv",
        index=False
    )

    print("\nFinal Results:")
    print(summary.to_string(index=False))


def main():

    print("Loading experiment results...")

    df = load_results()

    print("\nGenerating model performance graph...")
    plot_model_metrics(df)

    print("Generating accuracy graph...")
    plot_accuracy(df)

    print("Generating confusion matrices...")

    logistic_cm = np.load(
        RESULTS_DIR / "logistic_confusion_matrix.npy"
    )

    rf_cm = np.load(
        RESULTS_DIR / "random_forest_confusion_matrix.npy"
    )

    plot_confusion_matrix(
        logistic_cm,
        "Logistic Regression Confusion Matrix",
        "logistic_confusion_matrix.png"
    )

    plot_confusion_matrix(
        rf_cm,
        "Random Forest Confusion Matrix",
        "random_forest_confusion_matrix.png"
    )

    print("Generating training-time graph...")
    plot_training_time(df)

    print("Creating final results table...")
    create_summary(df)

    print("\n====================================")
    print("RESULT VISUALIZATION COMPLETED")
    print("====================================")

    print("\nGenerated files:")

    for file in sorted(PLOT_DIR.iterdir()):
        print("✓", file.name)

    print(
        "✓",
        RESULTS_DIR / "final_results_table.csv"
    )


if __name__ == "__main__":
    main()