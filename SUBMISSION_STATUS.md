# PFIV Guard — Submission Status and Final Actions

**Prepared:** 1 November 2026  
**Project team:** Pranav Dwivedi (24BBS0109), Aman Yadav (24BBS0168), Shourya Goyal (24BBS0132)  
**Institution:** Vellore Institute of Technology, Vellore

## Deliverables prepared in this pack

| Item | Pack status | What it is |
|---|---|---|
| Project report | READY FOR TEAM REVIEW | Editable DOCX and PDF; claims are scoped to saved evidence. |
| Final project presentation | READY FOR TEAM REVIEW | 15-slide PPTX and PDF. |
| IEEE-style paper | DRAFT PREPARED | Six-page two-column manuscript PDF, LaTeX source and bibliography; not submitted/published. |
| Video version | SCRIPT / STORYBOARD READY | Recording guide and narration prepared; actual screen capture/MP4 remains to be recorded by the team. |
| Patent / IP status | STATUS NOTE PREPARED | No application number/filing evidence supplied; status is NOT FILED / NO EVIDENCE. |
| Plagiarism / similarity report | INTERNAL PRE-CHECK ONLY | Citation/originality audit prepared; no official Turnitin/iThenticate report or similarity percentage is available. |
| GitHub | REPOSITORY PACKAGE READY | Clean source ZIP and push instructions; no GitHub repository URL exists until team pushes it. |
| Public website deployment | CONFIGURATION PREPARED | Deployment files included; no public hosted URL is evidenced yet. |
| Real-user validation | PROTOCOL READY | Facilitated study module and kit included; participant data and SUS responses have not been collected. |

## Verified implementation evidence

- Updated source tests: 29 passed in the preparation environment.
- WPFD/PFIV deterministic synthetic fixture validation: 10/10.
- Controlled PFIV security evaluation: 4/4 expected states matched.
- PFIV ablation: 3/4 decision categories changed (75% decision-change rate, not accuracy).
- UCI held-out model benchmark: Random Forest accuracy 97.65%, precision 98.03%, recall 96.63%, F1 97.33% (not live-web detection accuracy).
- Screenshot analysis: OCR/heuristic branch; not a trained screenshot/logo classifier.
- Live external threat-intelligence feeds are not connected.

## Must be completed by the team / institution

1. Re-run the updated project tests on the final laptop using the pinned requirements (`scikit-learn==1.6.1`).
2. Re-check the live Razorpay marketing homepage after the stricter transaction-intent gate change; do not claim the earlier false-trigger issue is resolved until the live re-test confirms it.
3. Push the clean repository to GitHub, initially private; add the actual URL after verifying the push.
4. Deploy through Streamlit Community Cloud or another approved host; add the public URL only after it loads and all workflows are rechecked.
5. Record and review the actual screen-demo MP4 using the video guide.
6. Conduct real participant usability sessions with consent; calculate task success, time, errors and SUS only from collected records.
7. Submit the final paper/report to the institution's approved similarity checker and attach the official export. This pack's originality audit is not a Turnitin/iThenticate certificate.
8. Ask the VIT IPR/technology-transfer office about ownership and filing strategy before public repository release or publication if patent protection is being considered.
9. Confirm author names, guide name, team number, course/subject details and contribution statements with the official project record.

## Important interpretation limits

- A fixture pass rate is not live-web phishing accuracy.
- A 75% ablation decision-change rate is not detection accuracy or statistical generalisation.
- A live ML probability produced by a UCI-compatible adapter is not a calibrated real-world probability.
- `Not Applicable` is appropriate when no active transaction step is found; unknown evidence must not automatically become phishing.
- UPI QR decoding does not verify recipient identity and does not initiate payment.
- Public deployment and real-user testing are external actions not completed by preparing files.
