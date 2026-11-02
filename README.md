# PFIV Guard

**Website Risk Assessment & Payment Flow Integrity Verification**

PFIV Guard is an academic defensive research prototype that helps a user understand what a public web page appears to do, whether the currently inspected page appears to be in a payment/transaction step, and what payment-flow evidence is observable in its static HTML.

The project keeps three tasks distinct:

1. **Website Purpose & Functionality Detection (WPFD):** explainable static-HTML heuristics estimate a page category (e.g., informational, e-commerce, banking, payment gateway, booking, productivity, education, news, government, healthcare, or unknown) and report visible functions/evidence.
2. **Website/URL risk assessment:** URL and HTML-derived features are passed through a Random Forest model trained on the UCI Phishing Websites dataset. The live feature adapter cannot obtain all historic UCI features; its live probability is an indicative model output, not a calibrated real-world probability.
3. **Payment Flow Integrity Verification (PFIV):** PFIV scoring and processor-path inspection run only when the inspected page shows strong active-transaction evidence: a payment-specific form, an explicit payment-action control plus transaction context, or a checkout/payment route plus transaction context. Generic marketing text such as “payment gateway”, “accept payments”, or “online payments” is not enough. It inspects observable sensitive form destinations, redirects, embedded resources, and known processor-domain consistency.

Additional input branches accept screenshots (OCR indicators and optional URL extraction) and QR images (URL / UPI payload decoding). UPI data is displayed for inspection only: the application never opens a payment app or initiates a transaction.

> **Safety and interpretation:** This is a research prototype, not a production security product. A purpose label does not authenticate a website owner. A low risk score is not a safety guarantee. A QR decode does not verify a payee. An OCR indicator score is not a phishing probability. The prototype does not connect to live VirusTotal/PhishTank/OpenPhish feeds, does not run browser JavaScript, and does not capture all browser runtime network requests.

## Architecture

```text
URL / Screenshot / QR
          |
          v
Static page fetch / OCR / QR decoding
          |
          v
Website Purpose & Functionality Detection (WPFD)
          |
          +----> Does this inspected page show transaction intent?
                       |                         |
                     No                         Yes
                       |                         |
                 PFIV: N/A             PFIV endpoint / processor /
                                       redirect / resource checks
          |
          v
URL/HTML Random Forest + OCR indicators + applicable PFIV evidence
          |
          v
Transparent weighted evidence fusion
          |
          v
Purpose + risk state + evidence + recommended caution
```

Purpose and transaction-intent detection are deliberately separate. A payment-gateway company's marketing homepage can be classified as **Payment Gateway / FinTech** while transaction intent remains **POTENTIAL** and PFIV remains **Not Applicable** because no active checkout or transaction step is visible. The full PFIV scoring/processor inspection is not invoked for such a page. A generic login/password form is not treated as a payment form.

## Main application features

- **Website analysis:** fetches public HTTP/HTTPS HTML with redirect and response-size bounds; detects page purpose; runs URL/HTML ML; applies PFIV only where transaction intent is detected.
- **Screenshot / OCR:** extracts visible text and URL strings, and reports cautious keyword/urgency indicators. No trained screenshot/logo model is included.
- **QR / UPI:** decodes an image; website URLs can be explicitly sent to website analysis; UPI URIs are parsed into display fields without initiating payment.
- **ML & explainability:** shows saved offline UCI benchmark metrics, feature importance and available SHAP artifacts.
- **Facilitated user study:** a researcher can record anonymous task observations and the 10-item SUS questionnaire after a participant has actually completed the tasks. It does not create participant results automatically.

## Run locally on Windows

Use Python 3.13 for the supplied local model environment, or use Python 3.12 for the deployment configuration. The bundled Random Forest artifact was serialized with scikit-learn 1.6.1; keep that version pinned.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Install the separate Tesseract OCR executable on Windows. If installed in the default location, set its path for the current terminal:

```powershell
$env:Path += ";C:\Program Files\Tesseract-OCR"
tesseract --version
```

Start the app:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed by Streamlit (normally `http://localhost:8501`).

### Local controlled PFIV fixtures only

The localhost fixture bypass is hidden by default. To expose the local-only checkbox during a controlled test session, set this environment variable **before** starting Streamlit:

```powershell
$env:PFIV_ENABLE_LOCAL_DEMO_UI = "1"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

In a second terminal, start the fixture server:

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

In the app sidebar, enable **Allow supplied localhost demo pages (testing only)** and use only the supplied `http://localhost:8000/data/demo_*.html` fixtures. Turn the control off after the test. Do not enable this on public deployment.

## Validation commands

### 1. Automated tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q -rs
```

### 2. Offline purpose / PFIV applicability fixtures (no server or ML model needed)

```powershell
.\.venv\Scripts\python.exe purpose_pfiv_evaluation.py
```

This evaluates ten synthetic HTML fixtures covering informational, e-commerce, banking, payment-gateway marketing, booking, login, and the four controlled payment-flow cases. It writes:

- `results/wpfd_pfiv_validation/wpfd_pfiv_fixture_results.csv`
- `results/wpfd_pfiv_validation/wpfd_pfiv_fixture_summary.json`

These are deterministic fixture checks, not live-web accuracy measurements. The current suite includes regression tests ensuring that payment-gateway marketing copy does not trigger PFIV and that the PFIV scoring function is not called for non-transaction pages.

### 3. Existing controlled PFIV security evaluation

Start the local fixture server as described above, enable the local-only demo checkbox, then run:

```powershell
.\.venv\Scripts\python.exe security_evaluation.py
.\.venv\Scripts\python.exe ablation_evaluation.py
```

The scripts use the purpose-aware PFIV applicability function. Refresh the CSV/JSON after code/model changes before quoting them in a report. The four controlled cases are not representative real-world attack prevalence and do not establish general detection accuracy.

## Facilitated user testing

Open the **Facilitated User Study** tab. A volunteer should first complete the four displayed tasks while a facilitator records completion, time, errors and help requests. Only after the tasks, the participant should answer the ten SUS items. Use a random code such as `P01`; do not record names, email addresses or sensitive information. The app computes the SUS score and offers a CSV download.

The user-study tab keeps records only in the active Streamlit session. Download the CSV after each session. It is a data-capture aid, not evidence that a study has already happened. Obtain the necessary faculty/department approval and informed consent before collecting participants' data. Never invent task outcomes, SUS scores, sample counts or satisfaction rates.

See `USER_TESTING_KIT.md` for the protocol and scoring explanation.

## Public deployment

The app is packaged for Streamlit Community Cloud:

- `requirements.txt` pins the Python dependencies and model-compatible scikit-learn version.
- `packages.txt` installs the external Linux `tesseract-ocr` executable.
- `.streamlit/config.toml` contains UI/server settings.
- `.github/workflows/tests.yml` runs automated tests and the ten-fixture WPFD/PFIV validation.
- `Dockerfile` provides an alternative container build.

Follow `DEPLOYMENT_GUIDE.md`. A public URL is not included in this source archive because deployment requires the project owner's GitHub/hosting account and an explicit deploy action. Do not describe the app as deployed until the host supplies a working public URL and it has been tested.

## Existing model results

The saved UCI Phishing Websites benchmark contains 11,055 rows and 30 features, with an 80/20 stratified split (8,844 train / 2,211 test; seed 42). Recorded results in `results/model_comparison.csv`:

| Model | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Logistic Regression | 92.81% | 93.44% | 90.10% | 91.74% |
| Random Forest | 97.65% | 98.03% | 96.63% | 97.33% |

These metrics describe the held-out UCI test split only. They are not the accuracy of live website analysis. The Random Forest pickle is serialized with scikit-learn 1.6.1; keep the exact pinned version when regenerating model-dependent outputs.

## Security, privacy and limitations

- URL fetching is passive HTTP GET only; the app never submits web forms.
- Local, private, loopback, link-local and reserved destinations are blocked by default; redirects are revalidated and capped. A narrow localhost fixture exception is available only in local development mode.
- Public demo mode has a per-browser-session request limit, but this is not a substitute for production-grade rate limiting, abuse monitoring, or a security review.
- The app inspects static HTML. JavaScript-rendered checkout interfaces, runtime API calls, and client-side redirects may not be observed.
- DNS validation and outbound fetching are best-effort protections; this academic prototype has not undergone a dedicated external SSRF penetration test. Do not deploy it as an unrestricted production URL-fetching service.
- Processor matching depends on `data/processors.json`, a finite reference registry that can be incomplete or outdated.
- WPFD is rule-based and explainable. Its heuristic confidence is evidence strength, not a calibrated probability or proof of site identity. Marketing language is deliberately separated from active transaction evidence; live-page regression checks are still required after changes.
- Screenshot/OCR scoring is heuristic; no trained screenshot/logo classifier is present.
- QR decoding does not verify URL ownership or UPI payee identity.
- Live threat-intelligence feeds are not connected.
- Evidence fusion uses configured transparent weights; it is not a learned meta-classifier.
- User-study results must come from real consenting participants. The source archive contains a capture tool and protocol, not participant findings.

## Project files of note

- `app.py` — Streamlit interface and facilitated user-study capture.
- `website_purpose.py` — website purpose and transaction intent heuristics.
- `analysis_pipeline.py` — shared purpose-aware URL/HTML/ML/PFIV pipeline.
- `bankshield_core.py` — safe fetching, page parsing and PFIV rules.
- `fusion.py` — evidence fusion.
- `live_ml.py` — Random Forest live-feature adapter.
- `visual_branch.py` — screenshot/OCR analysis.
- `qr_branch.py` — QR/UPI payload decoder.
- `purpose_pfiv_evaluation.py` — ten synthetic WPFD/PFIV fixtures (10/10 expected outcomes in the current authoring run).
- `tests/` — 29 automated tests passed in the current authoring environment; rerun after extracting this archive.
- `security_evaluation.py`, `ablation_evaluation.py` — controlled PFIV evaluation scripts.
- `IEEE_Paper/` — IEEE-style paper source and PDF.
- `USER_TESTING_KIT.md` — actual user-test protocol and measures.
- `DEPLOYMENT_GUIDE.md` — GitHub and Streamlit Community Cloud instructions.

## Submission and release notes

- `GITHUB_RELEASE_STEPS.md` explains private-first GitHub setup and deployment handoff.
- `SUBMISSION_STATUS.md` records which academic deliverables are prepared and which require team/institution action.
- `LICENSE_STATUS.md` records that no open-source licence has been selected; do not assume reuse rights.

## Information Security — Review 3 materials

The following Review 3 supporting documents are maintained in the repository:

- [British Airways 2018 incident case study](docs/IS_REVIEW_3_CASE_STUDY_BA_2018.md) — incident summary, authoritative timeline, impact, root cause, Review 1 threat-model link, PFIV Guard prevent/detect/miss analysis, safe simulation procedure and recommendations.
- [Review 1 threat-model mapping](docs/IS_REVIEW_3_THREAT_MODEL_MAPPING.md) — protected assets, attacker capabilities, attack types, incident-stage mapping and system coverage.
- [Results, comparison, limitations and future work](docs/IS_REVIEW_3_RESULTS_LIMITATIONS_FUTURE_WORK.md) — UCI model results, controlled PFIV evaluation, ablation, reproduction commands, limitations and research roadmap.
- [Individual contribution statement](docs/IS_REVIEW_3_INDIVIDUAL_CONTRIBUTIONS.md) — draft based on the Review 1 responsibility allocation; each member must verify and add actual evidence before submission.
- [Design choices and security mechanisms](docs/IS_REVIEW_3_DESIGN_AND_SECURITY_MECHANISMS.md).
- [Final Review 3 presentation outline](docs/IS_REVIEW_3_PRESENTATION_OUTLINE.md).

### Reproduce the safe British Airways-style PFIV simulation

Run from the repository root using the pinned dependencies (Python 3.12 is recommended):

```powershell
python incident_simulation_ba2018.py
python -m pytest -q tests/test_incident_simulation_ba2018.py
```

The simulation uses offline synthetic HTML and a reserved .example domain. It makes no network requests, submits no forms, and uses no real credentials or payment data. It writes a JSON result to results/incident_simulations/ba2018_pfiv_simulation_results.json. Preserve the actual terminal output and JSON result as Review 3 evidence; do not report expected results as measured results before running it.

The GitHub Actions workflow runs the repository test suite and WPFD/PFIV fixture validation after pushes and pull requests. Check the latest workflow run before recording the final test count/status in the review report.
