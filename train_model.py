from pathlib import Path
import json
import time

import joblib
import numpy as np
import pandas as pd

from ucimlrepo import fetch_ucirepo

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
RESULT_DIR = BASE_DIR / "results"

DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)

RANDOM_STATE = 42
TEST_SIZE = 0.20


def load_uci_dataset():
    print("Downloading UCI Phishing Websites dataset...")

    dataset = fetch_ucirepo(id=327)

    X = dataset.data.features.copy()
    y = dataset.data.targets.copy()

    if isinstance(y, pd.DataFrame):
        y = y.iloc[:, 0]

    X = X.apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(y, errors="coerce")

    valid_rows = X.notna().all(axis=1) & y.notna()

    X = X.loc[valid_rows].reset_index(drop=True)
    y = y.loc[valid_rows].reset_index(drop=True)

    # UCI encoding:
    # -1 = phishing
    #  1 = legitimate
    y = y.map({-1: 1, 1: 0})

    if y.isna().any():
        raise ValueError("Unexpected target values found in the dataset.")

    y = y.astype(int)

    return X, y


def evaluate_model(name, model, X_train, X_test, y_train, y_test):

    start = time.perf_counter()

    model.fit(X_train, y_train)

    train_time = time.perf_counter() - start

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, zero_division=0)
    recall = recall_score(y_test, predictions, zero_division=0)
    f1 = f1_score(y_test, predictions, zero_division=0)

    cm = confusion_matrix(y_test, predictions)

    print(f"\n===== {name} =====")
    print(f"Accuracy  : {accuracy:.4f}")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")
    print(f"Training Time : {train_time:.4f} sec")

    print("\nConfusion Matrix:")
    print(cm)

    return model, {
        "Model": name,
        "Accuracy": round(accuracy, 4),
        "Precision": round(precision, 4),
        "Recall": round(recall, 4),
        "F1": round(f1, 4),
        "Training_Time_sec": round(train_time, 4)
    }, cm


def main():

    X, y = load_uci_dataset()

    print("\nDataset shape:")
    print(X.shape)

    print("\nClass distribution:")
    print(
        pd.Series(y)
        .map({0: "Legitimate", 1: "Phishing"})
        .value_counts()
    )

    print("\nMissing values:")
    print(int(X.isna().sum().sum()))

    print("\nFeature count:")
    print(X.shape[1])

    # Save cleaned dataset
    cleaned = X.copy()
    cleaned["target"] = y

    cleaned.to_csv(
        DATA_DIR / "uci_phishing_clean.csv",
        index=False
    )

    # 80/20 stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y
    )

    print("\nTrain/Test Split:")
    print("Training samples :", len(X_train))
    print("Testing samples  :", len(X_test))

    # Baseline model
    logistic_model = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            max_iter=2000,
            random_state=RANDOM_STATE
        ))
    ])

    # Main model
    random_forest = RandomForestClassifier(
        n_estimators=300,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced"
    )

    results = []

    logistic_model, logistic_results, logistic_cm = evaluate_model(
        "Logistic Regression",
        logistic_model,
        X_train,
        X_test,
        y_train,
        y_test
    )

    results.append(logistic_results)

    rf_model, rf_results, rf_cm = evaluate_model(
        "Random Forest",
        random_forest,
        X_train,
        X_test,
        y_train,
        y_test
    )

    results.append(rf_results)

    # Save models
    joblib.dump(
        logistic_model,
        MODEL_DIR / "logistic_regression.pkl"
    )

    joblib.dump(
        rf_model,
        MODEL_DIR / "random_forest.pkl"
    )

    # Save test split
    X_test.to_csv(
        RESULT_DIR / "X_test.csv",
        index=False
    )

    y_test.to_csv(
        RESULT_DIR / "y_test.csv",
        index=False
    )

    # Save comparison
    results_df = pd.DataFrame(results)

    results_df.to_csv(
        RESULT_DIR / "model_comparison.csv",
        index=False
    )

    # Save RF feature importance
    feature_importance = pd.DataFrame({
        "Feature": X.columns,
        "Importance": rf_model.feature_importances_
    }).sort_values(
        "Importance",
        ascending=False
    )

    feature_importance.to_csv(
        RESULT_DIR / "feature_importance.csv",
        index=False
    )

    # Save confusion matrices
    np.save(
        RESULT_DIR / "logistic_confusion_matrix.npy",
        logistic_cm
    )

    np.save(
        RESULT_DIR / "random_forest_confusion_matrix.npy",
        rf_cm
    )

    metadata = {
        "dataset": "UCI Phishing Websites",
        "uci_id": 327,
        "instances": int(len(X)),
        "features": int(X.shape[1]),
        "test_size": TEST_SIZE,
        "train_size": int(len(X_train)),
        "test_size_samples": int(len(X_test)),
        "random_state": RANDOM_STATE,
        "target_mapping": {
            "0": "Legitimate",
            "1": "Phishing"
        },
        "models": [
            "Logistic Regression",
            "Random Forest"
        ]
    }

    (RESULT_DIR / "experiment_metadata.json").write_text(
        json.dumps(metadata, indent=4),
        encoding="utf-8"
    )

    print("\n========================================")
    print("ML TRAINING COMPLETED")
    print("========================================")

    print("\nGenerated files:")

    for path in [
        DATA_DIR / "uci_phishing_clean.csv",
        MODEL_DIR / "logistic_regression.pkl",
        MODEL_DIR / "random_forest.pkl",
        RESULT_DIR / "model_comparison.csv",
        RESULT_DIR / "feature_importance.csv",
        RESULT_DIR / "logistic_confusion_matrix.npy",
        RESULT_DIR / "random_forest_confusion_matrix.npy",
        RESULT_DIR / "experiment_metadata.json"
    ]:
        print("✓", path)


if __name__ == "__main__":
    main()