from pathlib import Path
import json
import numpy as np
import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parent
RESULTS = BASE / "results"
SECURITY = RESULTS / "security_evaluation"
ABLATION = RESULTS / "ablation"
PLOTS = RESULTS / "plots"
SHAP = RESULTS / "shap"

st.set_page_config(
    page_title="BankShield AI — Review 2",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ BankShield AI")
st.subheader("Review 2 — Implementation & Results Dashboard")
st.caption("End-to-end project evidence: ML, explainability, PFIV, security evaluation and ablation.")

# ---------- helpers ----------
def exists(path):
    return Path(path).exists()


def read_csv(path):
    if exists(path):
        return pd.read_csv(path)
    return None


def read_json(path):
    if exists(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return None

# ---------- implementation checklist ----------
st.markdown("## Implementation Status")
checks = [
    ("Streamlit application", exists(BASE / "app.py")),
    ("Trained Random Forest", exists(BASE / "models" / "random_forest.pkl")),
    ("Logistic Regression baseline", exists(BASE / "models" / "logistic_regression.pkl")),
    ("Model comparison results", exists(RESULTS / "model_comparison.csv")),
    ("Confusion matrices", exists(RESULTS / "random_forest_confusion_matrix.npy") and exists(RESULTS / "logistic_confusion_matrix.npy")),
    ("SHAP analysis", exists(SHAP / "shap_feature_importance.csv") and exists(SHAP / "local_phishing_explanation.csv")),
    ("Security evaluation", exists(SECURITY / "security_evaluation_results.csv")),
    ("PFIV ablation study", exists(ABLATION / "pfiv_ablation_results.csv")),
]
cols = st.columns(4)
for i, (label, ok) in enumerate(checks):
    cols[i % 4].metric(label, "Ready" if ok else "Pending")

# ---------- ML ----------
st.markdown("---")
st.markdown("## 1. Machine Learning Experiment")

model_df = read_csv(RESULTS / "model_comparison.csv")
if model_df is not None:
    display = model_df.copy()
    for col in ["Accuracy", "Precision", "Recall", "F1"]:
        if col in display.columns:
            display[col] = (display[col] * 100).round(2)
    display = display.rename(columns={
        "Accuracy": "Accuracy (%)",
        "Precision": "Precision (%)",
        "Recall": "Recall (%)",
        "F1": "F1 (%)",
        "Training_Time_sec": "Training Time (s)",
    })
    st.dataframe(display, use_container_width=True, hide_index=True)

    rf_rows = model_df[model_df["Model"].eq("Random Forest")]
    if not rf_rows.empty:
        rf = rf_rows.iloc[0]
        a, b, c, d = st.columns(4)
        a.metric("RF Accuracy", f"{rf['Accuracy']*100:.2f}%")
        b.metric("RF Precision", f"{rf['Precision']*100:.2f}%")
        c.metric("RF Recall", f"{rf['Recall']*100:.2f}%")
        d.metric("RF F1", f"{rf['F1']*100:.2f}%")
else:
    st.warning("Model comparison results not found.")

# ---------- confusion matrices ----------
st.markdown("### Confusion Matrices")
cm1, cm2 = st.columns(2)
for col, filename, title in [
    (cm1, "logistic_confusion_matrix.npy", "Logistic Regression"),
    (cm2, "random_forest_confusion_matrix.npy", "Random Forest"),
]:
    path = RESULTS / filename
    if exists(path):
        mat = np.load(path)
        df = pd.DataFrame(mat, index=["Actual Legitimate", "Actual Phishing"], columns=["Predicted Legitimate", "Predicted Phishing"])
        col.write(title)
        col.dataframe(df, use_container_width=True)

# ---------- feature importance ----------
st.markdown("### Random Forest Feature Importance")
fi = read_csv(RESULTS / "feature_importance.csv")
if fi is not None:
    st.dataframe(fi.head(10), use_container_width=True, hide_index=True)

# ---------- SHAP ----------
st.markdown("---")
st.markdown("## 2. Explainable AI — SHAP")

if exists(SHAP / "shap_global_bar.png"):
    st.image(str(SHAP / "shap_global_bar.png"), caption="Global SHAP feature importance", use_container_width=True)

if exists(SHAP / "shap_summary.png"):
    st.image(str(SHAP / "shap_summary.png"), caption="SHAP summary plot", use_container_width=True)

local = read_csv(SHAP / "local_phishing_explanation.csv")
selected = read_json(SHAP / "selected_sample.json")
if selected:
    st.write("Selected test sample")
    x, y, z = st.columns(3)
    x.metric("Actual", selected.get("actual_label", "-"))
    y.metric("Prediction", selected.get("predicted_label", "-"))
    z.metric("Phishing Probability", f"{selected.get('phishing_probability', 0)*100:.2f}%")
if local is not None:
    st.dataframe(local.head(10), use_container_width=True, hide_index=True)

# ---------- security evaluation ----------
st.markdown("---")
st.markdown("## 3. Security Evaluation")
security_df = read_csv(SECURITY / "security_evaluation_results.csv")
if security_df is not None:
    st.dataframe(security_df, use_container_width=True, hide_index=True)
    summary = read_json(SECURITY / "security_evaluation_summary.json")
    if summary:
        s1, s2, s3 = st.columns(3)
        s1.metric("Cases Passed", f"{summary.get('passed_cases', 0)}/{summary.get('total_cases', 0)}")
        s2.metric("Controlled Pass Rate", f"{summary.get('pass_rate_percent', 0):.2f}%")
        valid_times = pd.to_numeric(security_df["Total Analysis Time (s)"], errors="coerce")
        s3.metric("Average Total Time", f"{valid_times.mean():.4f}s")
else:
    st.warning("Security evaluation results not found.")

# ---------- overhead ----------
st.markdown("### Performance / Timing")
if security_df is not None:
    timing_cols = [
        "Test Case",
        "Fetch Time (s)",
        "PFIV Analysis Time (s)",
        "ML Inference Time (s)",
        "Total Analysis Time (s)",
    ]
    available = [c for c in timing_cols if c in security_df.columns]
    st.dataframe(security_df[available], use_container_width=True, hide_index=True)

# ---------- ablation ----------
st.markdown("---")
st.markdown("## 4. PFIV Ablation Study")
ablation_df = read_csv(ABLATION / "pfiv_ablation_results.csv")
if ablation_df is not None:
    st.dataframe(ablation_df, use_container_width=True, hide_index=True)

    summary = read_json(ABLATION / "pfiv_ablation_summary.json")
    if summary:
        a1, a2 = st.columns(2)
        a1.metric("Decision Changes Due to PFIV", f"{summary.get('decision_changes_due_to_pfiv', 0)}/{summary.get('cases', 0)}")
        a2.metric("Decision Change Rate", f"{summary.get('decision_change_rate_percent', 0):.2f}%")
else:
    st.warning("PFIV ablation results not found.")

# ---------- key findings ----------
st.markdown("---")
st.markdown("## 5. Review 2 Key Findings")
st.write("• Random Forest is the main URL/HTML model; Logistic Regression is the experimental baseline.")
st.write("• PFIV detects payment-flow anomalies such as unexpected sensitive endpoints and processor mismatch.")
st.write("• SHAP provides global and individual explanations for the URL/HTML model.")
st.write("• Controlled security scenarios and processing time are recorded for Review 2 evaluation.")
st.write("• The PFIV ablation isolates the contribution of the payment-flow branch.")

st.caption("Academic note: controlled 4-case security/ablation results are proof-of-concept evidence, not a general accuracy estimate. Offline ML metrics refer to the UCI test split.")
