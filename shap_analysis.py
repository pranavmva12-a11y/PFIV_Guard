from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "random_forest.pkl"
X_TEST_PATH = BASE_DIR / "results" / "X_test.csv"
Y_TEST_PATH = BASE_DIR / "results" / "y_test.csv"

RESULTS_DIR = BASE_DIR / "results" / "shap"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def main():

    print("Loading trained Random Forest model...")
    model = joblib.load(MODEL_PATH)

    print("Loading test data...")
    X_test = pd.read_csv(X_TEST_PATH)
    y_test = pd.read_csv(Y_TEST_PATH).iloc[:, 0]

    print("Test shape:", X_test.shape)

    print("\nCreating SHAP explainer...")
    explainer = shap.TreeExplainer(model)

    print("Calculating SHAP values...")
    shap_values = explainer.shap_values(X_test)

    # Handle SHAP output differences across versions
    if isinstance(shap_values, list):
        # Binary classification:
        # class 0 = legitimate
        # class 1 = phishing
        phishing_shap = shap_values[1]
    else:
        shap_array = np.asarray(shap_values)

        if shap_array.ndim == 3:
            # shape can be (samples, features, classes)
            phishing_shap = shap_array[:, :, 1]
        else:
            phishing_shap = shap_array

    phishing_shap = np.asarray(phishing_shap)

    print("SHAP matrix shape:", phishing_shap.shape)

    # -------------------------------------------------
    # 1. Global feature importance using mean(|SHAP|)
    # -------------------------------------------------

    mean_abs_shap = np.abs(phishing_shap).mean(axis=0)

    shap_importance = pd.DataFrame({
        "Feature": X_test.columns,
        "Mean_Absolute_SHAP": mean_abs_shap
    }).sort_values(
        "Mean_Absolute_SHAP",
        ascending=False
    )

    shap_importance.to_csv(
        RESULTS_DIR / "shap_feature_importance.csv",
        index=False
    )

    # -------------------------------------------------
    # 2. Global SHAP bar plot
    # -------------------------------------------------

    plt.figure(figsize=(10, 7))

    top_n = min(15, len(shap_importance))

    top_data = shap_importance.head(top_n).sort_values(
        "Mean_Absolute_SHAP"
    )

    plt.barh(
        top_data["Feature"],
        top_data["Mean_Absolute_SHAP"]
    )

    plt.xlabel("Mean Absolute SHAP Value")
    plt.ylabel("Feature")
    plt.title("Top Features Influencing Phishing Predictions")
    plt.tight_layout()

    plt.savefig(
        RESULTS_DIR / "shap_global_bar.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    # -------------------------------------------------
    # 3. SHAP summary / beeswarm plot
    # -------------------------------------------------

    plt.figure(figsize=(11, 8))

    shap.summary_plot(
        phishing_shap,
        X_test,
        show=False,
        max_display=15
    )

    plt.tight_layout()

    plt.savefig(
        RESULTS_DIR / "shap_summary.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    # -------------------------------------------------
    # 4. Explain one phishing sample
    # -------------------------------------------------

    probabilities = model.predict_proba(X_test)

    phishing_probabilities = probabilities[:, 1]

    phishing_indices = np.where(y_test.to_numpy() == 1)[0]

    if len(phishing_indices) == 0:
        raise ValueError("No phishing sample found in the test dataset.")

    # Choose the phishing test example with highest confidence
    selected_index = phishing_indices[
        np.argmax(phishing_probabilities[phishing_indices])
    ]

    sample = X_test.iloc[selected_index]
    sample_shap = phishing_shap[selected_index]

    local_explanation = pd.DataFrame({
        "Feature": X_test.columns,
        "Feature_Value": sample.values,
        "SHAP_Value": sample_shap,
        "Absolute_SHAP": np.abs(sample_shap)
    }).sort_values(
        "Absolute_SHAP",
        ascending=False
    )

    local_explanation.to_csv(
        RESULTS_DIR / "local_phishing_explanation.csv",
        index=False
    )

    # -------------------------------------------------
    # 5. Save selected sample information
    # -------------------------------------------------

    selected_prediction = int(
        model.predict(X_test.iloc[[selected_index]])[0]
    )

    selected_probability = float(
        probabilities[selected_index, 1]
    )

    sample_info = {
        "test_sample_index": int(selected_index),
        "actual_label": (
            "Phishing"
            if int(y_test.iloc[selected_index]) == 1
            else "Legitimate"
        ),
        "predicted_label": (
            "Phishing"
            if selected_prediction == 1
            else "Legitimate"
        ),
        "phishing_probability": round(
            selected_probability,
            6
        )
    }

    (RESULTS_DIR / "selected_sample.json").write_text(
        json.dumps(sample_info, indent=4),
        encoding="utf-8"
    )

    # -------------------------------------------------
    # 6. Print top explanations
    # -------------------------------------------------

    print("\n========================================")
    print("GLOBAL SHAP FEATURE IMPORTANCE")
    print("========================================")

    print(
        shap_importance.head(10).to_string(index=False)
    )

    print("\n========================================")
    print("SELECTED SAMPLE EXPLANATION")
    print("========================================")

    print(
        json.dumps(
            sample_info,
            indent=4
        )
    )

    print("\nTop features influencing selected prediction:")

    print(
        local_explanation.head(10).to_string(index=False)
    )

    print("\n========================================")
    print("SHAP ANALYSIS COMPLETED")
    print("========================================")

    print("\nGenerated files:")

    for file in [
        RESULTS_DIR / "shap_feature_importance.csv",
        RESULTS_DIR / "shap_global_bar.png",
        RESULTS_DIR / "shap_summary.png",
        RESULTS_DIR / "local_phishing_explanation.csv",
        RESULTS_DIR / "selected_sample.json"
    ]:
        print("✓", file)


if __name__ == "__main__":
    main()