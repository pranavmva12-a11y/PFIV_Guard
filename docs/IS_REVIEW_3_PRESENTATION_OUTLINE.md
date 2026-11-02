# IS Review 3 — Final Presentation Content Outline

**Project:** PFIV Guard — Website Risk Assessment and Payment Flow Integrity Verification  
**Team 20:** Aman Yadav, Shourya Goyal, Pranav Dwivedi  
**Purpose:** Slide-ready outline for the IS Review 3 final presentation. Insert only screenshots and evidence captured from the team's actual current system.

---

## Slide 1 — Title

**PFIV Guard**  
Website Risk Assessment and Payment Flow Integrity Verification

Information Security — Review 3: Final Project Completion

Team 20  
Aman Yadav | Shourya Goyal | Pranav Dwivedi  
Guide: Harini N

**Visual:** Current application homepage screenshot (capture after successful deployment; not included here).

## Slide 2 — Problem and motivation

- Phishing pages can imitate genuine banking, merchant and payment interfaces.
- Visual appearance and HTTPS alone do not establish where sensitive payment information is sent.
- A genuine processor name or logo does not prove that the complete payment path is consistent.
- Users need an understandable assessment before entering sensitive information.

**Research question:** Can a user-side system assess the observable sensitive-payment path and explain its consistency or risk?

## Slide 3 — Objectives and contribution

**Objectives**
- Detect phishing-related URL and HTML indicators.
- Estimate website purpose and transaction intent separately.
- Inspect payment-specific form destinations and observable processor/path evidence.
- Present explainable risk findings and cautious recommendations.
- Support screenshot/OCR and QR/UPI payload inspection.

**Focused contribution:** Payment Flow Integrity Verification (PFIV), integrated with website-purpose-aware analysis.

**Avoid claiming:** Novelty of generic multimodal phishing detection, standalone processor identification or generic visual phishing detection.

## Slide 4 — System architecture

**Inputs:** URL | Screenshot | QR image

**Processing branches**
1. URL normalization, safe fetch and static HTML parsing.
2. WPFD: purpose and visible functionality estimation.
3. Transaction-intent check: decide whether PFIV applies.
4. URL/HTML Random Forest + explainability.
5. PFIV: payment form endpoints, processor consistency, redirects and embedded resources.
6. Screenshot/OCR indicators and QR/UPI decoding.
7. Weighted evidence fusion.
8. Result: purpose + risk classification + PFIV state + evidence + cautionary recommendation.

**Visual:** Use an updated architecture diagram consistent with current code. Mark live threat feeds and browser runtime analysis as not implemented.

## Slide 5 — Design choices

- Purpose classification is separated from active payment transaction detection.
- PFIV runs only when payment/transaction evidence is observed.
- Login credentials are distinguished from payment-specific fields.
- Unknown or insufficient evidence yields Needs Review/Unverifiable rather than automatic phishing.
- A processor visible in a script/iframe alone is not proof of a verified payment path.
- URL/HTML model, screenshot/OCR and PFIV are kept as separate evidence branches.

## Slide 6 — Security mechanisms

- HTTP/HTTPS-only URL validation; embedded credentials and unsupported schemes rejected.
- Local/private/link-local/reserved IP and internal host targets blocked by default.
- DNS resolution checks and redirect revalidation.
- Maximum five redirects; 2 MB response bound; 5-second connect and 10-second read timeout.
- Per-browser-session limit: 12 analyses per 10 minutes.
- Local fixture bypass hidden/disabled by default.
- Passive inspection only: no form submission, real card data, OTP or payment transaction.

**Caveat:** SSRF and DNS-rebinding protections have not received an independent penetration test.

## Slide 7 — Implementation and repository

- Streamlit research prototype.
- URL/HTML analysis and Random Forest inference.
- SHAP/global feature-importance outputs.
- WPFD and transaction-intent heuristics.
- PFIV processor/endpoint/redirect inspection.
- Screenshot/OCR and QR/UPI branches.
- README, requirements, automated tests, model/data/results and reproducibility instructions.

**Repository:** https://github.com/pranavmva12-a11y/PFIV_Guard  
**Repository visibility:** Private.

**Visual:** Current GitHub repository root screenshot showing key files. Do not use a mock repository screenshot.

## Slide 8 — Offline ML results

**Dataset:** UCI Phishing Websites — 11,055 samples, 30 features, stratified 80/20 split, seed 42.

| Metric | Logistic Regression | Random Forest |
|---|---:|---:|
| Accuracy | 92.81% | 97.65% |
| Precision | 93.44% | 98.03% |
| Recall | 90.10% | 96.63% |
| F1 | 91.74% | 97.33% |

**Interpretation:** Random Forest outperformed the Logistic Regression baseline on the recorded held-out split.

**Caveat:** These values are offline UCI test-set metrics, not live website accuracy.

## Slide 9 — PFIV evaluation and ablation

**Controlled PFIV fixtures:** 4/4 expected states matched.
- Legitimate path → Verified
- External attacker endpoint → Suspicious
- Processor mismatch → Suspicious
- Unverifiable path → Unverifiable

**Ablation:** 3/4 controlled final decisions changed when PFIV was included (75% decision-change observation).

**Caveat:** Four fixtures do not establish real-world detection accuracy. The 75% is not accuracy.

## Slide 10 — Real-world incident: British Airways 2018

- Attacker used compromised third-party Swissport credentials to access BA's remote-access environment.
- Attacker moved into wider BA systems.
- Website JavaScript was modified so a copy of payment-card information went to attacker-controlled BAways.com.
- The normal checkout process continued while the additional data-copy path operated.
- ICO final notice estimated 429,612 individuals' data may have been accessed.
- ICO final penalty: £20 million (16 October 2020).

**Authoritative source:** UK ICO British Airways Penalty Notice, case COM0783542, 16 October 2020.

**Visual:** Timeline from the case-study document. Ensure the team has confirmed no other team selected this incident.

## Slide 11 — Incident timeline and root cause

**Timeline highlights**
- 22 June 2018: initial access through compromised Swissport credentials.
- 26 July 2018: access to plaintext log files containing card details.
- 14–25 August: malicious JavaScript changes.
- 21 August–5 September: card-data skimming active.
- 5 September: third party alerts BA; BA contains malicious code and blocks paths.
- 6–7 September: notifications.
- 16 October 2020: final ICO penalty notice.

**Root-cause categories**
- MFA not applied to all remote-access applications.
- Insufficient privilege boundaries and network segmentation.
- Privileged credentials stored in files.
- Test-only logging feature retained in production; sensitive card data stored in plaintext.
- JavaScript integrity and security monitoring gaps.

## Slide 12 — Review 1 threat-model mapping

**Assets:** Credentials, Payment information, Payment-flow integrity, User trust, Banking identity.

**Strongly related Review 1 threats:** Endpoint tampering; redirect/intermediary manipulation; domain deception.

**Not established in BA notice:** QR-based redirection, fake payment gateway, processor impersonation, visual clone, phishing as the exact initial credential-theft method.

**Key distinction:** The incident used the genuine BA site; this was not primarily a cloned fake bank page.

## Slide 13 — PFIV Guard: would it prevent, detect or miss?

| Incident stage | PFIV Guard assessment |
|---|---|
| Third-party credentials / MFA gap | Miss — no identity/MFA enforcement |
| Citrix breakout/lateral movement | Miss — no internal network telemetry |
| Plaintext credentials/log files | Miss — no internal file/log inspection |
| JavaScript code modification | Partial at best; first-party code change not compared against a trusted script baseline |
| Runtime card-data copy to BAways.com | Likely miss — no full browser runtime request observation |
| Counterfactual visible malicious form action | Could detect — static payment endpoint extraction |
| Counterfactual external script src | Could flag for review — not proof of maliciousness |

**Conclusion:** PFIV Guard is a complementary user-side inspection aid, not a control that would have stopped BA's initial network compromise.

## Slide 14 — Safe incident simulation

Four offline synthetic cases:
1. Legitimate Stripe control.
2. Visible form endpoint diversion to a reserved .example domain.
3. External script host indicator.
4. Inline JavaScript exfiltration string that current static inspection does not extract.

**Safety:** no network requests, no real BA/attacker domains, no payment submissions, no actual credentials or card details.

**Evidence to display:** actual JSON output and passing test summary after the team runs the commands. Until then mark simulation execution as pending.

## Slide 15 — Gaps and recommendations

- MFA for all remote and third-party access.
- Least privilege, network segmentation and supplier access restrictions.
- Remove card/CVV from logs and enforce production configuration controls.
- Script integrity controls, CSP/SRI and payment-page script monitoring.
- Browser-observed runtime network destination monitoring.
- Central logging, anomaly detection and privileged-access monitoring.
- Expand PFIV corpus and independent testing.
- Conduct SSRF/DNS-rebinding security assessment.
- Add live threat intelligence only with freshness and provenance.

## Slide 16 — Limitations and future work

**Limitations**
- One offline UCI dataset and one train/test split.
- Live ML adapter lacks some historical features.
- Four controlled PFIV cases only.
- Static HTML; no browser JavaScript execution/runtime network observation.
- Finite processor registry; no live TI feed in recorded evaluation.
- OCR is heuristic; no trained screenshot classifier.
- Fixed evidence-fusion weights.
- No independent SSRF penetration test.

**Future work**
- Larger labelled PFIV test corpus and cross-dataset validation.
- Runtime browser evidence and script integrity.
- Live threat intelligence with timestamps.
- Better processor-registry provenance.
- Calibrated purpose/transaction thresholds and learned fusion if enough data is collected.
- Real participant usability study with consent.

## Slide 17 — Individual contribution

Use the verified member contribution statements from the contribution document. The Review 1 role allocation is only an initial plan; each member must confirm actual work and supply evidence.

- Aman Yadav — planned: Team Lead, UI/UX, survey, prototype, usability evaluation.
- Shourya Goyal — planned: Backend/security, PFIV, testing, data.
- Pranav Dwivedi — planned: Integration, architecture, review, documentation.

Show commit/file/test evidence per member.

## Slide 18 — Conclusion and Q&A

- PFIV Guard combines website-purpose awareness, URL/HTML phishing analysis and payment-flow integrity evidence.
- Random Forest outperformed Logistic Regression on the recorded UCI test split.
- Four controlled PFIV scenarios matched expected states; ablation altered three of four controlled decisions.
- The BA case study shows why payment-flow monitoring must be complemented by identity, network, script-integrity and runtime controls.
- PFIV Guard is an academic defensive prototype, not a production security guarantee.

**Final message:** “Look beyond the page appearance — inspect the observable payment path, explain the evidence, and be honest about what remains unseen.”

---

## Speaker preparation and evidence

Before presenting:
1. Run the offline simulation and preserve actual output.
2. Run the unit and fixture tests and preserve summaries.
3. Confirm the British Airways incident is unique to the team.
4. Verify all individual contribution statements.
5. Insert actual application screenshots, current architecture, repository screenshots and real test-output screenshots.
6. Do not insert a successful live-demo claim until the deployment is confirmed separately.
