# PFIV Guard — Project Handover and Next Actions

This archive contains the updated academic prototype formerly titled **BankShield AI**. The app display name is now **PFIV Guard**. The core contribution remains Payment Flow Integrity Verification (PFIV); Website Purpose & Functionality Detection (WPFD) is a context layer that estimates the inspected page's apparent purpose and transaction intent.

## What changed in this update

1. Added explainable static-HTML WPFD categories and evidence output.
2. Separated website purpose from transaction intent. A payment company's marketing homepage is not automatically treated as a checkout page.
3. Added purpose-aware PFIV applicability: normal informational pages and ordinary login-only forms return PFIV Not Applicable; PFIV runs when transaction-specific evidence is observed.
4. Tightened the `Verified` state: a processor name in a script/iframe alone is insufficient. A payment-specific sensitive-form destination must be observed and match a known processor, with no observed suspicious external/intermediary domain.
5. Added 10 deterministic synthetic WPFD/PFIV fixtures and validation output.
6. Added a facilitator-side anonymous usability-study tab, consent gate, task metrics and standard 10-item SUS scoring/export. It contains no participant results until real sessions are conducted.
7. Added Streamlit Community Cloud, Linux Tesseract, GitHub Actions and Docker configuration.
8. Added an IEEE conference-style research-report draft, source and references.

## Validation in the preparation environment

- `python -m compileall -q .` — passed.
- `python -m pytest -q -rs` — **27 passed**.
- `python purpose_pfiv_evaluation.py` — **10/10 synthetic fixtures passed**.
- `python security_evaluation.py` — **4/4 controlled PFIV states matched**.
- `python ablation_evaluation.py` — **3/4 controlled decisions changed (75% decision-change rate)**.

The 10-fixture results and four controlled PFIV results are deterministic fixture checks, not live-web accuracy estimates. The 75% ablation figure is not model accuracy.

### Model-version compatibility note

The supplied Random Forest pickle was serialized with scikit-learn 1.6.1 and `requirements.txt` pins that version. The current preparation container has scikit-learn 1.8.0 and emitted `InconsistentVersionWarning` when the pickle was loaded for the final security/ablation rerun. The PFIV fixture states were still matched, but **regenerate model-dependent risk/probability outputs in an environment installed from the pinned `requirements.txt` before using fresh scores in a formal submission**. The user's previous Windows environment reported scikit-learn 1.6.1.

## Run locally on Windows

From PowerShell in the project root:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:Path += ";C:\Program Files\Tesseract-OCR"
tesseract --version
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL shown by Streamlit (normally `http://localhost:8501`). Do not enable local fixture bypass for normal use.

## Run validation

```powershell
.\.venv\Scripts\python.exe -m pytest -q -rs
.\.venv\Scripts\python.exe purpose_pfiv_evaluation.py
```

For the local controlled payment-flow scripts, start a second terminal with:

```powershell
.\.venv\Scripts\python.exe -m http.server 8000 --bind 127.0.0.1
```

Then run, from the project root:

```powershell
.\.venv\Scripts\python.exe security_evaluation.py
.\.venv\Scripts\python.exe ablation_evaluation.py
```

Keep the local fixture server limited to the supplied fixtures. Stop it when the evaluation finishes.

## Public deployment status

Deployment files are prepared (`requirements.txt`, `packages.txt`, `.streamlit/config.toml`, GitHub Actions workflow, Dockerfile, `DEPLOYMENT_GUIDE.md`). **No public URL is included** because the owner must push the source to GitHub, authenticate to the hosting provider and explicitly deploy. Follow `DEPLOYMENT_GUIDE.md`, then test the actual hosted URL.

Do not deploy as an unrestricted public URL-fetching service without an independent SSRF/network-security review, global rate limiting/abuse monitoring and post-deployment smoke tests.

## Real-user study status

The app has a **Facilitated User Study** tab. It can record four task outcomes, observed times, errors, help requests and the ten SUS responses, then export an anonymous CSV. Records exist only in the active Streamlit session until downloaded. The `USER_TESTING_KIT.md` contains the participant instructions, consent language, tasks and scoring method.

**No real participant records are included in this archive.** Invite volunteer participants only after the applicable faculty/department approval and informed consent. Do not invent participants, task outcomes, timings or SUS results. The user study is not complete until sessions actually happen.

## IEEE-style report

- `IEEE_Paper/pfiv_guard_ieee_paper.pdf` — five-page two-column academic report draft.
- `IEEE_Paper/pfiv_guard_ieee_paper.tex` — editable LaTeX source.
- `IEEE_Paper/references.bib` — bibliography source.
- `IEEE_Paper/REPORT_STATUS.md` — evidence and limitation record.

This is an IEEE-format course/research draft, **not an IEEE-published or peer-reviewed paper**. It explicitly states that public deployment and participant-based usability testing are pending.

## Privacy note for the distributable archive

An additional QR screenshot in the uploaded source contained a personal payment-recipient identifier. It has been omitted from this distributable copy. The bundled synthetic `data/demo_qr_upi.png` remains available for demonstration. The original user-uploaded ZIP is not modified.


## Submission status snapshot (2026-11-01)

- Current source label: PFIV Guard (formerly BankShield AI).
- Purpose-aware transaction gate tightened: generic payment marketing copy is not sufficient to trigger PFIV.
- The complete PFIV scoring/processor inspection is invoked only after the transaction-intent gate returns active.
- Synthetic WPFD/PFIV fixtures: 10/10.
- Automated tests in the current authoring environment: 29 passed.
- Existing controlled PFIV security evaluation: 4/4.
- Existing four-case ablation: 3/4 decisions changed (75% decision-change rate, not accuracy).
- Public deployment: configuration prepared; public URL pending owner deployment.
- Real user testing/SUS: protocol and capture UI prepared; participant data not collected in this archive.
- IEEE-style paper: draft prepared, not submitted/published.
- Patent: not filed / no filing evidence provided.
- Plagiarism: external Turnitin/iThenticate report not generated; only an internal citation/originality pre-check is supplied.
