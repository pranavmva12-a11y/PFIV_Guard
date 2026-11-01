from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
import shap


BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "random_forest.pkl"
X_TEST_PATH = BASE_DIR / "results" / "X_test.csv"
Y_TEST_PATH = BASE_DIR / "results" / "y_test.csv"
MODEL_RESULTS_PATH = BASE_DIR / "results" / "model_comparison.csv"
FEATURE_IMPORTANCE_PATH = BASE_DIR / "results" / "feature_importance.csv"

SHAP_DIR = BASE_DIR / "results" / "shap"


def load_random_forest():
    return joblib.load(MODEL_PATH)


def load_test_data():
    X_test = pd.read_csv(X_TEST_PATH)
    y_test = pd.read_csv(Y_TEST_PATH).iloc[:, 0]
    return X_test, y_test


def load_model_results():
    return pd.read_csv(MODEL_RESULTS_PATH)


def load_feature_importance():
    return pd.read_csv(FEATURE_IMPORTANCE_PATH)


def get_selected_phishing_sample():
    X_test, y_test = load_test_data()
    model = load_random_forest()

    probabilities = model.predict_proba(X_test)[:, 1]

    phishing_indices = np.where(
        y_test.to_numpy() == 1
    )[0]

    if len(phishing_indices) == 0:
        raise ValueError("No phishing sample found.")

    selected_index = phishing_indices[
        np.argmax(probabilities[phishing_indices])
    ]

    return X_test, y_test, selected_index


def explain_selected_sample():
    import json

    X_test, y_test = load_test_data()

    model = load_random_forest()

    local_csv = SHAP_DIR / "local_phishing_explanation.csv"
    sample_json = SHAP_DIR / "selected_sample.json"

    # Use already-generated SHAP explanation if available
    if local_csv.exists() and sample_json.exists():

        explanation = pd.read_csv(local_csv)

        with open(sample_json, "r", encoding="utf-8") as f:
            sample_info = json.load(f)

        return {
            "index": sample_info["test_sample_index"],
            "actual": sample_info["actual_label"],
            "prediction": sample_info["predicted_label"],
            "probability": sample_info["phishing_probability"],
            "explanation": explanation
        }

    # Otherwise calculate SHAP only for one sample
    probabilities = model.predict_proba(X_test)[:, 1]

    phishing_indices = np.where(
        y_test.to_numpy() == 1
    )[0]

    if len(phishing_indices) == 0:
        raise ValueError("No phishing sample found.")

    selected_index = phishing_indices[
        np.argmax(probabilities[phishing_indices])
    ]

    sample = X_test.iloc[[selected_index]]

    explainer = shap.TreeExplainer(model)

    shap_values = explainer.shap_values(sample)

    if isinstance(shap_values, list):
        phishing_values = shap_values[1][0]
    else:
        shap_array = np.asarray(shap_values)

        if shap_array.ndim == 3:
            phishing_values = shap_array[0, :, 1]
        else:
            phishing_values = shap_array[0]

    explanation = pd.DataFrame({
        "Feature": X_test.columns,
        "Value": sample.iloc[0].values,
        "SHAP Value": phishing_values
    })

    explanation["Absolute SHAP"] = (
        explanation["SHAP Value"].abs()
    )

    explanation = explanation.sort_values(
        "Absolute SHAP",
        ascending=False
    )

    prediction = int(
        model.predict(sample)[0]
    )

    probability = float(
        model.predict_proba(sample)[0, 1]
    )

    return {
        "index": int(selected_index),
        "actual": (
            "Phishing"
            if int(y_test.iloc[selected_index]) == 1
            else "Legitimate"
        ),
        "prediction": (
            "Phishing"
            if prediction == 1
            else "Legitimate"
        ),
        "probability": probability,
        "explanation": explanation
    }


def get_shap_images():
    return {
        "bar": SHAP_DIR / "shap_global_bar.png",
        "summary": SHAP_DIR / "shap_summary.png"
    }