# PFIV Guard IEEE-style report status

This is an IEEE conference-style academic paper draft for internal review. It is not an IEEE-published, accepted, or peer-reviewed paper.

## Verified from the prepared project snapshot
- UCI Phishing Websites benchmark metadata: 11,055 rows, 30 features; stratified 80/20 split; random state 42; 8,844 train / 2,211 test.
- Saved offline metrics: Logistic Regression and Random Forest values in `../results/model_comparison.csv`.
- Saved Random Forest confusion matrix: `../results/random_forest_confusion_matrix.npy`.
- Ten synthetic WPFD/PFIV fixtures: 10/10 expected outputs matched after the transaction-gate update.
- Four controlled PFIV fixtures: 4/4 saved expected PFIV states matched in the existing security evaluation output.
- Four-case PFIV ablation: 3/4 final decision categories changed; this is not accuracy.
- Automated test suite: 29 tests passed in the current authoring environment.
- Regression rule: generic payment-gateway marketing copy alone does not invoke full PFIV scoring/processor inspection. The PFIV function is gated behind the active transaction-intent decision.

## Live-page observation and required recheck
A public Razorpay marketing-homepage run in an earlier build displayed Payment Gateway / FinTech but also incorrectly marked transaction intent as DETECTED, with no sensitive payment form, no payment iframe, and no actual redirect chain. The gate was tightened to require a payment-specific form, an explicit payment-action control plus transaction context, or a checkout/payment route plus transaction context. The synthetic payment-gateway marketing fixture now produces POTENTIAL / Not Applicable, and tests confirm the full PFIV scoring function is not invoked for it. **The live Razorpay page must be reanalysed after deployment or on the target Windows machine before claiming that this live-page false trigger is resolved.**

## Explicitly not completed / not claimed
- No real-user usability sessions or SUS participant data are included.
- The facilitated-study UI is a data-capture tool, not evidence that a user study was conducted.
- No public hosted URL is included; deployment files are prepared but deployment requires repository-owner authentication and a host action.
- No live VirusTotal, PhishTank, OpenPhish, or equivalent external threat-intelligence feed is connected.
- Screenshot analysis is OCR/heuristic based; no trained screenshot/logo classifier is included.
- WPFD is a static-HTML heuristic, not a trained or calibrated classifier.
- No external SSRF penetration test has been completed.
- No patent application number, filing receipt, or grant evidence was supplied; patent status is reported as not filed / not evidenced, not pending.
- No Turnitin/iThenticate similarity score was generated; a local citation/originality pre-check is not an institutional plagiarism report.

## Model serialization compatibility note
The bundled Random Forest artifact was serialized with scikit-learn 1.6.1 and `requirements.txt` pins that version. The current authoring environment has scikit-learn 1.8.0. The automated tests and synthetic WPFD/PFIV fixtures do not require loading the pickled model. Model-dependent scores/timing should be regenerated only in an environment installed from the pinned `requirements.txt`; do not use a fresh 1.8.0-pickle load as a replacement for the saved 1.6.1 benchmark outputs.
