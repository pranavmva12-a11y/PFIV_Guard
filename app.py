"""PFIV Guard (formerly BankShield AI) - multi-input defensive research prototype."""
from __future__ import annotations

import json
import hashlib
import os

import pandas as pd
from pathlib import Path

import streamlit as st

from bankshield_core import load_processor_map, normalize_url
from analysis_pipeline import analyze_url_input
from visual_branch import analyze_screenshot
from qr_branch import decode_qr_image
from ml_module import (
    load_model_results,
    load_feature_importance,
    explain_selected_sample,
    get_shap_images,
)
from usability_study import SUS_ITEMS, USABILITY_TASKS, build_participant_record

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
PROCESSOR_FILE = DATA_DIR / "processors.json"

st.set_page_config(page_title="PFIV Guard", page_icon="🛡️", layout="wide")
load_processor_map(str(PROCESSOR_FILE))
PROCESSORS = json.loads(PROCESSOR_FILE.read_text(encoding="utf-8"))


def safe_analyze(url: str, state_key: str, *, visual_score=None, allow_local=False):
    """Run common analysis, applying a small per-session demo request limit."""
    try:
        now = __import__("time").time()
        window_seconds = 600
        request_times = [t for t in st.session_state.get("analysis_request_times", []) if now - t < window_seconds]
        if len(request_times) >= 12:
            raise RuntimeError("This browser session has reached the 12-analysis / 10-minute demo limit. Please wait before trying again.")
        request_times.append(now)
        st.session_state["analysis_request_times"] = request_times
        with st.spinner("Inspecting page purpose, URL/HTML evidence, and PFIV applicability..."):
            result = analyze_url_input(
                url,
                visual_score=visual_score,
                allow_local_fixture=allow_local,
            )
        st.session_state[state_key] = result
        st.session_state[state_key + "_error"] = None
    except Exception as exc:
        st.session_state[state_key] = None
        st.session_state[state_key + "_error"] = str(exc)


def render_analysis_result(result: dict, key_prefix: str = "result"):
    """Show the common URL-analysis output regardless of input source."""
    if not result:
        return
    payment = result["payment"]
    fusion = result["fusion"]
    live_ml = result["live_ml"]
    website_purpose = result.get("website_purpose", {})
    transaction_intent = result.get("transaction_intent", {})

    st.subheader("Website Purpose & Functionality")
    purpose_cols = st.columns(3)
    purpose_cols[0].metric("Detected Purpose", website_purpose.get("label", "Unknown"))
    purpose_cols[1].metric("Evidence Strength", website_purpose.get("confidence_label", "Low"))
    purpose_cols[2].metric("Transaction Intent", transaction_intent.get("status", "Unknown"))
    detected_functions = website_purpose.get("detected_functions", [])
    if detected_functions:
        st.write("**Detected page functions:** " + " · ".join(detected_functions))
    st.caption("Purpose labels are static-HTML heuristics. They do not verify website ownership, reputation, or safety.")
    with st.expander("Why this website purpose was selected"):
        st.write("**Purpose evidence**")
        st.write(website_purpose.get("evidence", []) or ["No strong category-specific evidence was found."])
        st.write("**Inspected page signals**")
        st.json(website_purpose.get("page_signals", {}))
        st.write("**Transaction intent assessment**")
        st.write(transaction_intent.get("reason", "No explanation available."))

    st.subheader("Final Assessment")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Risk Score", f"{fusion['score']}/100")
    c2.metric("Classification", fusion["label"])
    c3.metric("Payment Flow", payment["status"])
    c4.metric("Analysis Time", f"{result['timings']['total_seconds']:.2f}s")

    if fusion["label"] == "High Risk":
        st.error("High Risk — do not enter sensitive payment information.")
    elif fusion["label"] == "Suspicious":
        st.warning("Suspicious or unverifiable — verify independently before entering sensitive information.")
    else:
        st.success("No high-risk signal was produced by the current prototype. This is not a guarantee that the site is safe.")

    st.caption(f"Analysed URL: {result['normalized_url']} | HTTP {result['http_status']} | {result['content_type']}")
    if result.get("page_title"):
        st.write(f"**Page title:** {result['page_title']}")

    st.markdown("### Live URL Machine Learning")
    ml1, ml2 = st.columns(2)
    ml1.metric("ML Prediction", live_ml["label"])
    if result["ml_available"]:
        ml2.metric("Phishing Probability", f"{result['ml_score']:.2f}%")
        st.caption("Live prediction from the trained Random Forest using a UCI-compatible feature adapter. This probability is not the offline test-set accuracy.")
    else:
        ml2.metric("Phishing Probability", "Unavailable")
        st.warning(result.get("ml_error") or "The ML branch did not run.")
    if result.get("visual_score") is not None:
        st.info(f"Screenshot/OCR indicator score included in fusion: {result['visual_score']:.1f}/100. This is a heuristic indicator score, not a calibrated probability.")

    with st.expander("Live feature vector"):
        st.json(live_ml.get("features", {}))

    st.markdown("### Payment Flow Integrity Verification (PFIV)")
    st.caption(f"PFIV applicability: {payment.get('applicability', 'Unknown')} — {transaction_intent.get('reason', '')}")
    page = payment["page"]
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Payment Page", "Detected" if page["payment_page_detected"] else "Not Detected")
    p2.metric("Processor", payment["processor"] or "Not identified")
    p3.metric("Processor Consistency", payment["processor_consistency"])
    p4.metric("External Endpoints", len(payment["external_endpoints"]))

    st.markdown("### Evidence")
    evidence = result.get("evidence", [])
    if evidence:
        for item in evidence:
            st.write("• " + item)
    else:
        st.write("No additional evidence messages were produced.")

    with st.expander("Sensitive payment endpoints"):
        st.json([
            {"Method": form["method"], "Action": form["action"], "Domain": form["domain"]}
            for form in page.get("payment_forms", [])
        ])
    with st.expander("Redirect / intermediary domains"):
        st.write("Redirect chain")
        st.json(payment.get("redirect_chain", []))
        st.write("Intermediary domains")
        st.json(payment.get("intermediate_domains", []))
    with st.expander("Embedded payment resources"):
        st.write("Iframes")
        st.json(page.get("iframe_domains", []))
        st.write("Scripts")
        st.json(page.get("script_domains", []))
    with st.expander("Processor reference registry"):
        st.json(PROCESSORS)
    with st.expander("Timing detail"):
        st.json(result["timings"])
    with st.expander("Limitations for this result"):
        for limitation in result.get("limitations", []):
            st.write("• " + limitation)
    st.download_button(
        "Download analysis report (JSON)",
        data=json.dumps(result, indent=2, ensure_ascii=False),
        file_name="pfiv_guard_analysis.json",
        mime="application/json",
        key=f"download_{key_prefix}",
    )


def show_saved_result(state_key: str, label: str):
    error = st.session_state.get(state_key + "_error")
    if error:
        st.error(f"{label} failed: {error}")
    result = st.session_state.get(state_key)
    if result:
        render_analysis_result(result, key_prefix=state_key)


st.title("🛡️ PFIV Guard")
st.caption("Website Risk Assessment + Website Purpose Detection + Payment Flow Integrity Verification")
st.info(
    "Research prototype: do not enter real card details. The app fetches public URLs for passive inspection, "
    "never submits payment forms, and never initiates a QR/UPI payment. Results are risk indicators, not a safety guarantee."
)

with st.sidebar:
    st.header("Analysis modules")
    st.write("✅ Website purpose & function detection")
    st.write("✅ URL / HTML analysis + Random Forest")
    st.write("✅ Payment Flow Integrity Verification")
    st.write("✅ Screenshot OCR evidence")
    st.write("✅ QR / UPI payload inspection")
    st.write("✅ ML & SHAP explainability")
    st.divider()
    # The local fixture bypass is hidden by default. Enable its UI only in an
    # explicitly configured local development environment; never expose it on cloud demos.
    show_local_demo_control = os.getenv("PFIV_ENABLE_LOCAL_DEMO_UI", "0").strip() == "1"
    allow_local_demo = False
    if show_local_demo_control:
        allow_local_demo = st.checkbox(
            "Allow supplied localhost demo pages (testing only)",
            value=False,
            help="Development-only switch for the named localhost:8000/data/demo_*.html fixtures.",
        )
        if allow_local_demo:
            st.warning("Local demo mode enabled. Use only the bundled /data/demo_*.html fixtures.")
    st.caption("Local demo fixture bypass is disabled unless PFIV_ENABLE_LOCAL_DEMO_UI=1 is set by the local operator.")
    st.caption("Live external threat-intelligence feeds are not connected in this build.")

url_tab, screenshot_tab, qr_tab, ml_tab, study_tab = st.tabs([
    "🌐 Website Analysis",
    "🖼️ Screenshot / OCR",
    "🔳 QR / UPI",
    "📊 ML & Explainability",
    "🧪 Facilitated User Study",
])

# -----------------------------------------------------------------------------
# URL INPUT
# -----------------------------------------------------------------------------
with url_tab:
    st.subheader("Analyse a website or checkout URL")
    st.write("PFIV Guard first estimates the inspected page's purpose and transaction intent, then runs PFIV only when a transaction step is indicated.")
    url = st.text_input(
        "Website / checkout URL",
        placeholder="https://example.com/checkout",
        key="main_url_input",
    )
    st.caption("Public HTTP/HTTPS pages are supported. Local/private network destinations are blocked unless the supplied localhost demo option is enabled.")
    if st.button("Analyse URL", type="primary", use_container_width=True, key="analyse_main_url"):
        if not url.strip():
            st.error("Enter a website URL first.")
        else:
            safe_analyze(url, "main_url_result", allow_local=allow_local_demo)
    show_saved_result("main_url_result", "URL analysis")

# -----------------------------------------------------------------------------
# SCREENSHOT + OCR
# -----------------------------------------------------------------------------
with screenshot_tab:
    st.subheader("Screenshot analysis")
    st.write("Upload a screenshot of a website or checkout page. OCR extracts visible text; if a URL is visible, it can be sent to the common URL-analysis pipeline.")
    uploaded_screenshot = st.file_uploader(
        "Upload screenshot",
        type=["png", "jpg", "jpeg", "webp"],
        key="screenshot_upload",
    )
    screenshot_site_url = st.text_input(
        "Optional: website URL shown in this screenshot",
        placeholder="https://example.com/checkout",
        key="screenshot_site_url",
    )
    enable_ocr = st.checkbox("Enable OCR text extraction", value=True, key="screenshot_ocr_enabled")
    if uploaded_screenshot:
        current_screenshot_hash = hashlib.sha256(uploaded_screenshot.getvalue()).hexdigest()
        if st.session_state.get("screenshot_upload_hash") != current_screenshot_hash:
            st.session_state["screenshot_upload_hash"] = current_screenshot_hash
            st.session_state["screenshot_result"] = None
            st.session_state["screenshot_url_result"] = None
            st.session_state["screenshot_url_result_error"] = None
        st.image(uploaded_screenshot, caption="Uploaded screenshot", use_container_width=True)
        if st.button("Analyse screenshot", type="primary", key="analyse_screenshot"):
            visual_result = analyze_screenshot(uploaded_screenshot.getvalue(), enable_ocr)
            st.session_state["screenshot_result"] = visual_result
            st.session_state["screenshot_url_result"] = None
            st.session_state["screenshot_url_result_error"] = None
            if screenshot_site_url.strip():
                # A zero/no-read OCR result is not evidence of safety, so it is
                # displayed separately but not used to lower the URL risk score.
                screenshot_fusion_score = visual_result.get("risk_score", 0.0)
                if not visual_result.get("ocr_available") or screenshot_fusion_score <= 0:
                    screenshot_fusion_score = None
                safe_analyze(
                    screenshot_site_url,
                    "screenshot_url_result",
                    visual_score=screenshot_fusion_score,
                    allow_local=allow_local_demo,
                )

    else:
        if st.session_state.get("screenshot_upload_hash") is not None:
            st.session_state["screenshot_upload_hash"] = None
            st.session_state["screenshot_result"] = None
            st.session_state["screenshot_url_result"] = None
            st.session_state["screenshot_url_result_error"] = None

    visual_result = st.session_state.get("screenshot_result")
    if visual_result:
        st.markdown("### Screenshot/OCR evidence")
        v1, v2 = st.columns(2)
        v1.metric("OCR heuristic indicator score", f"{visual_result['risk_score']:.1f}/100")
        v2.metric("Text extraction confidence", visual_result.get("confidence", "Limited"))
        for item in visual_result.get("evidence", []):
            st.write("• " + item)
        if visual_result.get("detected_terms"):
            st.write("**Detected terms:** " + ", ".join(visual_result["detected_terms"]))
        if visual_result.get("extracted_urls"):
            st.write("**URLs found in screenshot text:**")
            for found_url in visual_result["extracted_urls"]:
                st.code(found_url)
            selected_url = st.selectbox(
                "Choose a URL extracted from the screenshot",
                options=visual_result["extracted_urls"],
                key="screenshot_extracted_url_choice",
            )
            if st.button("Analyse selected screenshot URL", type="primary", key="analyse_screenshot_extracted_url"):
                screenshot_fusion_score = visual_result.get("risk_score", 0.0)
                if not visual_result.get("ocr_available") or screenshot_fusion_score <= 0:
                    screenshot_fusion_score = None
                safe_analyze(
                    selected_url,
                    "screenshot_url_result",
                    visual_score=screenshot_fusion_score,
                    allow_local=allow_local_demo,
                )
        if visual_result.get("ocr_text"):
            with st.expander("Extracted OCR text"):
                st.text(visual_result["ocr_text"][:8000])
        st.caption("Screenshot-only score is a heuristic indicator score, not a trained computer-vision phishing probability. It cannot establish where data is sent.")
    show_saved_result("screenshot_url_result", "Screenshot URL analysis")

# -----------------------------------------------------------------------------
# QR INPUT
# -----------------------------------------------------------------------------
with qr_tab:
    st.subheader("QR code inspection")
    st.write("Upload a QR image. If it encodes a website URL, you can explicitly send that URL to the same URL/PFIV analysis pipeline.")
    uploaded_qr = st.file_uploader(
        "Upload QR code image",
        type=["png", "jpg", "jpeg", "webp"],
        key="qr_upload",
    )
    if uploaded_qr:
        current_qr_hash = hashlib.sha256(uploaded_qr.getvalue()).hexdigest()
        if st.session_state.get("qr_upload_hash") != current_qr_hash:
            st.session_state["qr_upload_hash"] = current_qr_hash
            st.session_state["qr_result"] = None
            st.session_state["qr_url_result"] = None
            st.session_state["qr_url_result_error"] = None
        st.image(uploaded_qr, caption="Uploaded QR image", width=280)
        if st.button("Decode QR", type="primary", key="decode_qr"):
            st.session_state["qr_result"] = decode_qr_image(uploaded_qr.getvalue())
            st.session_state["qr_url_result"] = None
            st.session_state["qr_url_result_error"] = None

    else:
        if st.session_state.get("qr_upload_hash") is not None:
            st.session_state["qr_upload_hash"] = None
            st.session_state["qr_result"] = None
            st.session_state["qr_url_result"] = None
            st.session_state["qr_url_result_error"] = None

    qr_result = st.session_state.get("qr_result")
    if qr_result:
        for item in qr_result.get("evidence", []):
            st.write("• " + item)
        if not qr_result.get("decoded"):
            st.warning("QR could not be decoded. Try a clearer image with the full code visible.")
        else:
            choices = [f"{i+1}. {entry['type']} — {entry['payload'][:85]}" for i, entry in enumerate(qr_result["items"])]
            selected_index = st.selectbox("Decoded QR payload", range(len(choices)), format_func=lambda idx: choices[idx], key="qr_payload_choice")
            item = qr_result["items"][selected_index]
            st.markdown("**Decoded payload**")
            st.code(item["payload"])
            if item["type"] == "upi_payment_uri":
                st.markdown("**Decoded UPI fields**")
                st.json(item.get("details", {}))
                st.warning("This QR contains a payment URI. BankShield does not initiate a payment or confirm the payee's identity. Verify the recipient and amount independently in your payment app.")
            elif item["is_web_url"]:
                st.caption(f"Recognised website URL: {item['web_url']}")
                if st.button("Analyse decoded URL", type="primary", key="analyse_qr_url"):
                    safe_analyze(item["web_url"], "qr_url_result", allow_local=allow_local_demo)
            else:
                st.info("This QR payload is not an HTTP/HTTPS URL, so the website-analysis pipeline cannot fetch it. Review the decoded content independently.")
    show_saved_result("qr_url_result", "QR URL analysis")

# -----------------------------------------------------------------------------
# MODEL / SHAP RESULTS
# -----------------------------------------------------------------------------
with ml_tab:
    st.header("Machine Learning & Explainability")
    st.write("Offline benchmark results from the UCI Phishing Websites dataset. These numbers describe the held-out test split, not live URL accuracy.")
    try:
        results = load_model_results()
        display_results = results.copy()
        for column in ["Accuracy", "Precision", "Recall", "F1"]:
            if column in display_results.columns:
                display_results[column] = (display_results[column] * 100).round(2)
        display_results = display_results.rename(columns={
            "Accuracy": "Accuracy (%)",
            "Precision": "Precision (%)",
            "Recall": "Recall (%)",
            "F1": "F1 (%)",
            "Training_Time_sec": "Training Time (s)",
        })
        st.dataframe(display_results, use_container_width=True, hide_index=True)
        st.subheader("Random Forest metrics")
        rf_rows = results[results["Model"] == "Random Forest"]
        if not rf_rows.empty:
            rf = rf_rows.iloc[0]
            a, b, c, d = st.columns(4)
            a.metric("Accuracy", f"{rf['Accuracy'] * 100:.2f}%")
            b.metric("Precision", f"{rf['Precision'] * 100:.2f}%")
            c.metric("Recall", f"{rf['Recall'] * 100:.2f}%")
            d.metric("F1 Score", f"{rf['F1'] * 100:.2f}%")
    except Exception as exc:
        st.warning(f"Model comparison results could not be loaded: {exc}")

    try:
        st.subheader("Random Forest feature importance")
        st.dataframe(load_feature_importance().head(10), use_container_width=True, hide_index=True)
    except Exception as exc:
        st.warning(f"Feature importance data could not be loaded: {exc}")

    try:
        st.subheader("SHAP explainability")
        shap_images = get_shap_images()
        if shap_images["bar"].exists():
            st.write("Global SHAP importance")
            st.image(str(shap_images["bar"]), use_container_width=True)
        if shap_images["summary"].exists():
            st.write("SHAP summary of feature contributions")
            st.image(str(shap_images["summary"]), use_container_width=True)
        if st.button("Explain a high-confidence phishing sample", type="primary", key="explain_sample"):
            explanation = explain_selected_sample()
            e1, e2, e3 = st.columns(3)
            e1.metric("Actual", explanation["actual"])
            e2.metric("Prediction", explanation["prediction"])
            e3.metric("Phishing Probability", f"{explanation['probability'] * 100:.2f}%")
            st.dataframe(explanation["explanation"].head(10), use_container_width=True, hide_index=True)
    except Exception as exc:
        st.warning(f"SHAP artifacts could not be displayed: {exc}")

# -----------------------------------------------------------------------------
# FACILITATED, ANONYMOUS USABILITY STUDY
# -----------------------------------------------------------------------------
with study_tab:
    st.header("Facilitated Usability Study")
    st.info(
        "Researcher/facilitator mode. Ask a volunteer to complete the four tasks first, "
        "then record observations and administer the 10-item SUS questionnaire. "
        "Do not collect names, email addresses, passwords, OTPs, or payment details."
    )
    st.markdown("**Suggested tasks**")
    for task_code, task_text in USABILITY_TASKS:
        st.write(f"**{task_code}:** {task_text}")
    st.caption("Use synthetic fixtures and public pages only. Participation should be voluntary; follow your faculty/department requirements before collecting study data.")

    with st.form("pfiv_guard_usability_form"):
        st.subheader("Anonymous participant record")
        participant_code = st.text_input("Participant code (e.g., P01; do not enter a name)", max_chars=20)
        consent_given = st.checkbox("The volunteer has received the study explanation and has voluntarily agreed to participate.")

        task_results = []
        st.subheader("Task observations (facilitator records these)")
        for task_code, task_text in USABILITY_TASKS:
            st.markdown(f"**{task_code} — {task_text}")
            c1, c2, c3 = st.columns(3)
            completed = c1.checkbox("Completed", key=f"study_{task_code}_completed")
            time_seconds = c2.number_input("Time (seconds)", min_value=0.0, max_value=3600.0, value=0.0, step=5.0, key=f"study_{task_code}_time")
            errors = c3.number_input("Errors", min_value=0, max_value=50, value=0, step=1, key=f"study_{task_code}_errors")
            help_needed = st.checkbox("Facilitator help was needed", key=f"study_{task_code}_help")
            task_results.append({
                "completed": completed,
                "time_seconds": time_seconds,
                "errors": errors,
                "help_needed": help_needed,
            })

        st.subheader("System Usability Scale (SUS)")
        st.caption("Answer after completing the tasks. 1 = Strongly disagree; 5 = Strongly agree.")
        sus_responses = []
        for index, question in enumerate(SUS_ITEMS, start=1):
            answer = st.selectbox(
                f"{index}. {question}",
                options=[0, 1, 2, 3, 4, 5],
                format_func=lambda value: "Choose a response" if value == 0 else f"{value} — " + {1: "Strongly disagree", 2: "Disagree", 3: "Neither agree nor disagree", 4: "Agree", 5: "Strongly agree"}[value],
                key=f"sus_q{index}",
            )
            sus_responses.append(answer)
        participant_comments = st.text_area("Optional anonymous comments (do not include identifying or sensitive details)", max_chars=1000)
        submitted = st.form_submit_button("Save anonymous participant record", type="primary", use_container_width=True)

    if submitted:
        if not consent_given:
            st.error("Do not save a record unless the volunteer has given informed, voluntary consent.")
        elif not participant_code.strip():
            st.error("Enter an anonymous participant code, not a person's name.")
        elif any(value == 0 for value in sus_responses):
            st.error("Please complete all 10 SUS responses after the tasks.")
        else:
            try:
                record = build_participant_record(participant_code, task_results, sus_responses, participant_comments)
                existing = st.session_state.setdefault("pfiv_user_study_records", [])
                if any(row.get("Participant_Code") == record["Participant_Code"] for row in existing):
                    st.error("That participant code already exists in this session. Use a unique anonymous code.")
                else:
                    existing.append(record)
                    st.session_state["pfiv_user_study_records"] = existing
                    st.success(f"Record saved for {record['Participant_Code']}. SUS score: {record['SUS_Score']:.1f}/100. Export the CSV before closing or refreshing the app.")
            except ValueError as exc:
                st.error(str(exc))

    records = st.session_state.get("pfiv_user_study_records", [])
    if records:
        study_df = pd.DataFrame(records)
        st.subheader("Session records")
        k1, k2, k3 = st.columns(3)
        k1.metric("Participants recorded", len(records))
        k2.metric("Mean SUS score", f"{study_df['SUS_Score'].mean():.1f}/100")
        k3.metric("Mean tasks completed", f"{study_df['Task_Success_Count'].mean():.2f}/4")
        st.dataframe(study_df[["Participant_Code", "SUS_Score", "Task_Success_Count", "Total_Errors", "Total_Help_Requests"]], use_container_width=True, hide_index=True)
        st.download_button(
            "Download anonymous usability-study CSV",
            data=study_df.to_csv(index=False).encode("utf-8"),
            file_name="pfiv_guard_usability_study.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption("Records are held in the current Streamlit session only. Download the CSV after each session; this app does not provide durable research storage.")
    else:
        st.caption("No participant data has been recorded in this session. Do not present an empty form as completed user testing.")

st.divider()
st.caption("PFIV Guard is an academic research prototype. URL fetching is passive; it never submits payment forms, initiates QR/UPI payments, or collects card data, CVV, OTPs, passwords, or PINs.")
