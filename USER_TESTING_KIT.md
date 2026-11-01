# PFIV Guard — Real-User Usability Testing Kit

**Status:** Protocol and in-app capture tool prepared. No participant results are bundled with this project. Conduct the sessions before claiming that user testing, SUS, or satisfaction evaluation is complete.

## 1. Study objective

Evaluate whether non-technical or mixed-experience users can:

1. identify what kind of page PFIV Guard inspected;
2. understand whether PFIV applies to the current page;
3. interpret URL/ML, OCR and QR evidence without confusing heuristic indicators with probabilities or guarantees; and
4. choose an appropriate safe next action.

This is a small formative academic usability study, not a population-representative experiment or a security-accuracy benchmark.

## 2. Participants and ethics

- Suggested pilot: 6–10 adult volunteers from the intended user group (e.g., university students / everyday web users), subject to faculty and institutional requirements.
- Include people with mixed technical familiarity; note the broad familiarity band only if your approved protocol requires it.
- Participation is voluntary. Explain the tasks, what is recorded, how the data will be used, and that the participant may stop at any time.
- Use anonymous codes only (P01, P02, ...). Do not collect names, email addresses, phone numbers, student IDs, account details, IP addresses, passwords, OTPs, CVV, card numbers, PINs, or actual payment data.
- Use synthetic fixtures and benign public pages. Never ask a participant to log in, submit a form, or initiate a payment.
- Obtain required faculty/department approval or exemption before collecting participant data. Store exported records in an institution-approved location.

### Short consent script

> “We are evaluating the usability of an academic website-risk and payment-flow demonstration. You will complete four short tasks and answer a 10-question usability questionnaire. We will record task completion, time, errors, help requests and your questionnaire answers using an anonymous code. Do not enter passwords, OTPs, card details or any real payment information. Participation is voluntary and you may stop at any time. Do you agree to participate?”

Record only whether consent was given; do not type a signature or identifying details into the app.

## 3. Environment preparation

- Use a laptop/desktop browser for the first pilot and record the device/browser category (do not collect unique device identifiers).
- Confirm that PFIV Guard starts and all demo files are present.
- Ensure Tesseract is available for screenshot/OCR tasks.
- Keep local fixture mode disabled except for the supervised synthetic PFIV mismatch task. Disable it immediately after.
- Reset the app/session before each participant where practical.
- Explain that the tool is a prototype and does not certify a site as safe.

## 4. Participant tasks and success criteria

| Task | Prompt to participant | Success criterion | Record |
|---|---|---|---|
| T1 — Page purpose | “Analyse this public informational page. Tell me what the page appears to be for and whether a payment-flow check applies.” | Correctly finds purpose panel and understands PFIV is Not Applicable when no active transaction step is detected. | Completion, seconds, errors, help, interpretation |
| T2 — Screenshot/OCR | “Upload the supplied synthetic checkout screenshot. Tell me one clue the system extracted and what the OCR score represents.” | Finds extracted text/URL and states that the OCR score is a heuristic indicator, not a phishing probability. | Completion, seconds, errors, help, interpretation |
| T3 — QR/UPI | “Decode the supplied UPI demo QR. Tell me the payee name and amount, and what the app has not verified.” | Reads decoded fields and states that decoding does not verify recipient identity or initiate a payment. | Completion, seconds, errors, help, interpretation |
| T4 — Explain result | “Review a result where ML and the final assessment differ. Explain why you should not treat the ML output alone as a safety guarantee and state a safe next step.” | Distinguishes the ML estimate from the final evidence-fusion result and chooses independent verification / not proceeding with sensitive entry while uncertain. | Completion, seconds, errors, help, interpretation |

Do not teach the answer during the task. If help is necessary, record the help request and what was explained. Stop a task if a participant attempts to enter real credentials or sensitive payment details.

## 5. Moderator observation rules

- Start timing when the task prompt has been read and the participant begins interaction.
- Stop timing when the participant states that the task is complete or abandons it.
- Count an error when the participant selects the wrong mode, submits invalid input, misunderstands a displayed field, or needs to backtrack because the interface was unclear. State your counting rule before sessions and apply it consistently.
- Record facilitator help separately from errors.
- For comprehension, use a simple rubric: 0 = incorrect / unsafe interpretation; 1 = partly correct or needs prompting; 2 = correct and independently explained.
- Write short anonymous observations; do not infer motivation or personal traits.

## 6. System Usability Scale (SUS)

After the tasks, ask the participant to answer all ten standard SUS items on a 1–5 scale:

1 = Strongly disagree; 2 = Disagree; 3 = Neither agree nor disagree; 4 = Agree; 5 = Strongly agree.

1. I think that I would like to use this system frequently.
2. I found the system unnecessarily complex.
3. I thought the system was easy to use.
4. I think that I would need the support of a technical person to be able to use this system.
5. I found the various functions in this system were well integrated.
6. I thought there was too much inconsistency in this system.
7. I would imagine that most people would learn to use this system very quickly.
8. I found the system very cumbersome to use.
9. I felt very confident using the system.
10. I needed to learn a lot of things before I could get going with this system.

### SUS scoring

- For odd-numbered items (1, 3, 5, 7, 9): contribution = response − 1.
- For even-numbered items (2, 4, 6, 8, 10): contribution = 5 − response.
- Sum the ten contributions and multiply by 2.5. The resulting SUS score ranges from 0 to 100.
- Do not call the score a percentage of users satisfied. SUS is a questionnaire score, not a satisfaction percentage.
- Report individual scores and descriptive group summaries (mean, median, range) with the sample size. Interpret small pilot samples cautiously.

The app's **Facilitated User Study** tab implements this scoring and creates an anonymous CSV download. Its records remain in the current Streamlit session; download after each participant.

## 7. Reporting formulas

- Task completion rate (%) = (completed task attempts ÷ total task attempts) × 100.
- Median successful-task time = median time among successfully completed attempts.
- Error count = sum of errors recorded under the pre-defined error rule.
- Help rate (%) = (task attempts with facilitator help ÷ total task attempts) × 100.
- Warning comprehension = report rubric 0/1/2 distribution for each task.
- SUS = calculate each participant's score, then report descriptive statistics for the actual sample.

Do not remove failed tasks from the denominator when reporting completion rate. Do not invent missing times or fill unobserved outcomes with assumed values.

## 8. Post-session questions

Ask, in open-ended form:

1. Which result or label was hardest to understand?
2. Was it clear why PFIV did or did not apply to the inspected page?
3. Did you understand the difference between the ML prediction and final risk assessment?
4. What one change would make the next action clearer?

## 9. Accessibility / interface inspection checklist

Record each item as Pass / Needs Improvement / Not Checked, with browser/device context:

- All primary functions are keyboard reachable.
- Focus indicator is visible and focus order is logical.
- Text and controls remain usable at 200% zoom.
- Layout reflows on a narrow/mobile viewport without horizontal scrolling for primary tasks.
- Text/background and control-state contrast meet the intended accessibility target (verify with a contrast analyser; do not infer from appearance alone).
- Risk states use text labels/icons as well as colour.
- Inputs have explicit labels and errors explain how to recover.
- Status and analysis progress are announced or otherwise perceivable.
- Uploaded file constraints and sensitive-data warnings are clear before analysis.

This checklist has not been fully audited automatically or by accessibility specialists. Mark untested items Not Checked.

## 10. Data template

The Streamlit study tab exports one CSV row per participant. A blank structure is also provided at `results/usability_template.csv`. No example participant results are included.

## 11. Limitations to state in the report

- Small convenience samples support formative improvement, not broad generalisation.
- The study evaluates usability of the current prototype, not real-world phishing detection accuracy.
- KLM estimates are analytical models; participant task timings are separate empirical measures.
- A participant's interpretation can be affected by prior technical experience; describe the sample and avoid overclaiming.
- The system itself is heuristic in the website-purpose branch and does not prove site ownership or transaction legitimacy.
