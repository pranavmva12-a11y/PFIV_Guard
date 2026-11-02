# IS Review 3 — Final Results, Comparison, Limitations and Future Work

**Project:** PFIV Guard (formerly BankShield AI)  
**Purpose:** Website Risk Assessment and Payment Flow Integrity Verification

## 1. Evaluation tracks and reporting rules

PFIV Guard has multiple evaluation tracks. They must be reported separately because they use different data, targets and test conditions.

1. **Offline URL/HTML ML benchmark:** evaluates a Random Forest and Logistic Regression on the held-out UCI Phishing Websites test split.
2. **Controlled PFIV scenarios:** checks whether designed local payment-flow fixtures produce expected PFIV states.
3. **PFIV ablation:** compares final risk decisions with and without PFIV on the same four controlled scenarios.
4. **WPFD/PFIV fixture validation and automated tests:** exercises purpose classification and software behavior using synthetic fixtures.
5. **Live website exploration:** exploratory checks against public websites; these are not a statistically labelled benchmark.

The offline ML metrics are not the accuracy of the complete live application. A 4/4 controlled PFIV result is not real-world detection accuracy. The 3/4 ablation decision-change observation is not accuracy or a success rate.

## 2. Offline ML benchmark

### 2.1 Dataset and setup

| Property | Recorded setup |
|---|---|
| Dataset | UCI Phishing Websites |
| Dataset size | 11,055 instances |
| Input features | 30 engineered features |
| Target | Phishing / legitimate |
| Training/test split | 80% / 20%, stratified |
| Training samples | 8,844 |
| Held-out test samples | 2,211 |
| Random seed | 42 |
| Baseline | StandardScaler + Logistic Regression (max_iter=2000, random_state=42) |
| Main model | Random Forest (300 trees, class_weight=balanced, n_jobs=-1, random_state=42) |

### 2.2 Recorded model comparison

| Metric | Logistic Regression | Random Forest |
|---|---:|---:|
| Accuracy | 92.81% | 97.65% |
| Precision | 93.44% | 98.03% |
| Recall | 90.10% | 96.63% |
| F1-score | 91.74% | 97.33% |

**Interpretation:** On the recorded 2,211-example held-out split, Random Forest outperformed the Logistic Regression baseline on all four reported metrics. This supports selecting Random Forest as the main offline model for this dataset and split.

**Important deployment distinction:** The live URL adapter maps available URL/page evidence into a UCI-compatible feature schema, but cannot obtain every historical feature from an arbitrary public webpage. Features such as web traffic, PageRank, search-engine index and backlinks may be unavailable and are represented with neutral values in the live compatibility layer. Therefore, the displayed live model score is an indicative model output, not a calibrated real-world phishing probability and not the offline 97.65% accuracy.

### 2.3 Explainability

The project includes global feature-importance artifacts and SHAP explanations for the URL/HTML model branch. The explanations describe feature contributions to the model output; they do not prove that a website is malicious or legitimate. The project does not claim that SHAP explains the separate PFIV rules or every fused risk contribution.

## 3. Controlled PFIV security evaluation

Four local HTML scenarios were used to check the expected state transitions. The application did not submit a form or process a payment.

| Scenario | Expected PFIV state | Recorded PFIV state | PFIV score | Recorded total time |
|---|---|---|---:|---:|
| Legitimate payment path | Verified | Verified | 0 | 1.0877 s |
| External attacker endpoint | Suspicious | Suspicious | 65 | 0.1739 s |
| Processor mismatch | Suspicious | Suspicious | 55 | 0.1574 s |
| Unverifiable payment path | Unverifiable | Unverifiable | 35 | 0.1595 s |

**Recorded result:** 4 of 4 controlled scenarios matched the expected PFIV state.

The four recorded total times average approximately **0.3946 seconds**. This is a descriptive mean from four controlled local runs, not a performance guarantee, production latency SLA or representative benchmark. The legitimate case was slower in the recorded run; live domain/metadata processing can introduce variation.

## 4. PFIV ablation study

The same four controlled scenarios were evaluated with PFIV evidence removed from fusion and then with PFIV included.

| Scenario | Without PFIV | With PFIV | Decision changed? |
|---|---|---|---|
| Legitimate payment | Legitimate (17.54) | Legitimate (12.28) | No |
| External attacker endpoint | Legitimate (17.70) | High Risk (65.00) | Yes |
| Processor mismatch | Legitimate (17.54) | High Risk (65.00) | Yes |
| Unverifiable payment | Legitimate (17.13) | Suspicious (35.00) | Yes |

**Recorded observation:** PFIV changed the final decision in 3 of 4 controlled cases (75%). This measures how often the designed cases changed their final label when the PFIV branch was added; it is not model accuracy, recall, precision or a real-world attack-detection rate.

The ablation supports the design rationale that payment-path evidence can materially influence decisions in the specific endpoint and mismatch cases that were constructed. A larger independent case set is required to quantify general performance.

## 5. WPFD/PFIV fixture validation and automated tests

The repository README records a ten-fixture purpose/PFIV validation with 10/10 expected outcomes and 29 automated tests passed in the previous authoring environment. These figures describe the recorded project validation state. They must be freshly reproduced after the current repository changes before being reported as the latest CI result.

The British Airways incident simulation added to the repository includes five additional regression tests. The simulation must be executed and its current test summary recorded before claiming those new cases passed.

### Reproduction commands (run from repository root)

**Windows PowerShell**

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q -rs
.\.venv\Scripts\python.exe purpose_pfiv_evaluation.py
.\.venv\Scripts\python.exe incident_simulation_ba2018.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_incident_simulation_ba2018.py
~~~

The Random Forest pickle was serialized with scikit-learn 1.6.1; use the repository's pinned dependency version rather than upgrading scikit-learn during reproduction.

### Evidence to retain

- Full output of pytest, including passed/failed/skipped summary.
- Full output of purpose_pfiv_evaluation.py.
- Generated results/wpfd_pfiv_validation/wpfd_pfiv_fixture_results.csv and summary JSON.
- Output of incident_simulation_ba2018.py and its JSON result.
- Dedicated incident test summary.
- GitHub Actions run status for the latest commit.

Do not use expected fixture outcomes as observed results before executing the commands.

## 6. Comparison with baseline and existing approaches

### 6.1 Measured comparison within this project

The Logistic Regression baseline and Random Forest were trained/evaluated on the same UCI dataset split and are therefore the project's directly comparable ML results. Random Forest had the higher recorded accuracy, precision, recall and F1.

The PFIV branch is not an alternative classifier trained on the UCI dataset. It is a separate rule/evidence branch evaluated on four controlled checkout scenarios. Its metrics must not be placed in the same accuracy column as Logistic Regression and Random Forest.

### 6.2 Comparison with literature

The Review 1 survey includes URL-based models, visual phishing models, explainable models and threat-intelligence-assisted approaches. Published performance values across those studies should not be ranked directly against PFIV Guard's 97.65% because the studies use different datasets, labels, preprocessing, splits, test prevalence and evaluation protocols.

The project's defensible distinction is functional rather than a claim of superior benchmark accuracy: PFIV Guard combines a URL/HTML ML branch with an explicit, user-side payment-flow evidence branch that considers sensitive form destinations, observed processor consistency, redirects/intermediaries and embedded resources. WPFD helps distinguish a page's business purpose from a current active payment step.

No direct reimplementation of Phishpedia, PhishIntention, URLTran or other literature baseline is claimed.

## 7. Limitations

1. **Dataset generalisation:** The ML metrics use one public, engineered UCI dataset and one stratified hold-out split. They do not establish performance on every current phishing campaign or banking/payment domain.
2. **Live feature coverage:** The live feature adapter cannot observe every historical UCI feature. Live outputs must be treated as indicative.
3. **PFIV sample size:** The PFIV security evaluation has four manually designed local scenarios. A larger labelled checkout corpus is required.
4. **Static HTML visibility:** The fetcher parses returned HTML. It does not execute browser JavaScript or observe every runtime fetch, XMLHttpRequest, sendBeacon, dynamically inserted script, service worker or client-side navigation.
5. **Processor registry:** Processor identification depends on a finite JSON reference list that may be incomplete, stale or region-specific. A match is not proof of merchant ownership or transaction safety.
6. **Threat intelligence:** Live VirusTotal, PhishTank and OpenPhish checks were not active in the recorded Review 2 quantitative experiment.
7. **Visual analysis:** Screenshot/OCR output is heuristic evidence. No trained screenshot/logo classifier or labelled visual benchmark is included.
8. **Fusion:** Evidence fusion uses configured fixed weights rather than a meta-classifier trained on a labelled dataset of branch outputs.
9. **False positives/negatives:** Exploratory public-site checks showed that static pages and marketing language can produce incomplete or misleading signals; broader calibration and independent tests are necessary.
10. **Operational security:** URL fetching has defensive URL/IP/redirect/size/time checks, but the prototype has not undergone an independent SSRF penetration test, DNS-rebinding assessment or production abuse review.
11. **Usability:** The facilitated user-study tab captures data but does not prove that participants have completed a study. Genuine consented participant results are needed before reporting usability scores.

## 8. Future work

### Near-term evaluation work
- Expand the PFIV corpus with legitimate, suspicious, unverifiable and edge-case checkout pages.
- Add multiple independent test sets and repeated timing measurements; report mean, median and dispersion.
- Preserve raw labelled fixture outputs so results can be reproduced and audited.
- Tune purpose/transaction-intent thresholds against a labelled validation set and track false-positive rates.

### Technical improvements
- Add safe browser-based runtime observation to identify unexpected checkout network destinations and dynamically inserted payment scripts.
- Consider script-integrity baselines, Subresource Integrity (SRI) awareness and Content Security Policy (CSP) inspection as supporting evidence, not as standalone proof.
- Improve processor registry provenance, update frequency and regional coverage.
- Add live threat-intelligence integration with source timestamps, API-limit handling and confidence/coverage labels.
- Improve screenshot analysis with a labelled visual dataset and a trained visual model, if required by the final project scope.
- Evaluate a learned fusion model only after collecting enough labelled branch-level examples; maintain transparent rules as a fallback.
- Conduct independent SSRF testing, rate-limit/abuse testing, privacy review and a deployment security assessment before any non-academic use.

### Research extensions
- Conduct an independent user study with informed consent and report task success, warning comprehension, decision time, user errors and SUS scores only from actual participants.
- Evaluate cross-dataset generalisation and drift.
- Compare static analysis against browser-observed runtime behaviour on controlled payment-flow fixtures.

## 9. Final conclusion

The recorded project results show that Random Forest performed better than Logistic Regression on the chosen UCI held-out split, while the PFIV branch correctly handled four designed payment-flow cases and changed three of four controlled final decisions in the ablation comparison. These findings support the prototype's architecture and the value of explicit payment-path evidence in the tested scenarios. They do not establish production-grade or real-world detection accuracy. The strongest final claim is that PFIV Guard provides an explainable research prototype combining website-purpose awareness, URL/HTML phishing signals and payment-flow integrity checks, with documented limits and a reproducible path for further evaluation.

## 10. Source documents

- README.md — installation, usage, architecture, reproduction and limitations.
- BankShield_Review2_Report.docx — recorded Review 2 metrics, controlled PFIV cases, ablation and timing.
- docs/IS_REVIEW_3_CASE_STUDY_BA_2018.md — incident case study and controlled incident simulation.
- UCI Machine Learning Repository, [Phishing Websites dataset, ID 327](https://archive.ics.uci.edu/dataset/327/phishing+websites).
