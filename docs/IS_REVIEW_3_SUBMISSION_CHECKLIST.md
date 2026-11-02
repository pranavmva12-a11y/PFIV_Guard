# IS Review 3 — Submission Readiness Checklist

**Project:** PFIV Guard  
**Team:** 20  
**Members:** Aman Yadav (24BBS0168), Shourya Goyal (24BBS0132), Pranav Dwivedi (24BBS0109)

This checklist tracks the IS Review 3 requirements other than the live deployment/demo, which is being handled separately.

## 1. Review 3 requirement tracker

| Teacher requirement | Repository evidence | Current state | Remaining action |
|---|---|---|---|
| Final source-code repository and README | Private GitHub repository; README has setup, use, architecture, reproducibility and links to Review 3 docs | Prepared | Team to confirm repository contains final code and no secrets/private test data |
| Final results and comparison | Results, limitations and future-work document; Review 2 recorded model/PFIV/ablation tables | Consolidated from recorded Review 2 evidence | Re-run current test suite and fixture scripts; attach fresh outputs |
| Design choices and security mechanisms | README, source modules, case-study and threat-model documents | Documented in source and supporting docs | Add final architecture/security screenshots or diagram to presentation |
| Real-world incident case study | British Airways 2018 incident case study; ICO penalty notice cited | Draft prepared | Confirm incident is unique to this team in the class |
| Incident summary, timeline and impact | Case-study document | Prepared from ICO notice | Review dates and source citations during final edit |
| Root cause and technical/process failures | Case-study document | Prepared | Team review |
| Mapping to Review 1 threat model | Separate threat-model mapping document; assets, attacker capabilities and attack types preserved | Prepared | Verify Review 1 wording matches submitted Review 1 copy |
| Prevent/detect/miss analysis | Incident-stage capability table | Prepared, with limitations stated | Review with faculty/team |
| Scaled-down incident simulation | Offline synthetic simulation script and five regression tests | Implemented in repository; execution not yet evidenced | Run commands and save actual output/JSON and test summary |
| Gaps and recommendations | Case-study recommendations and system limitations/future work | Prepared | Team review |
| Individual contribution statement | Draft based on Review 1 planned role allocation | Draft only | Each member confirms actual work and supplies evidence |
| Final consolidated report/PPT | Markdown source materials in repository | Content prepared across linked files | Assemble into required college format and add approved screenshots/evidence |

## 2. Repository links

- [Private GitHub repository](https://github.com/pranavmva12-a11y/PFIV_Guard)
- [README and reproduction instructions](../README.md)
- [British Airways 2018 incident case study](IS_REVIEW_3_CASE_STUDY_BA_2018.md)
- [Review 1 threat-model mapping](IS_REVIEW_3_THREAT_MODEL_MAPPING.md)
- [Results, comparison, limitations and future work](IS_REVIEW_3_RESULTS_LIMITATIONS_FUTURE_WORK.md)
- [Individual contribution statements](IS_REVIEW_3_INDIVIDUAL_CONTRIBUTIONS.md)
- [Design choices and security mechanisms](IS_REVIEW_3_DESIGN_AND_SECURITY_MECHANISMS.md)
- [Final presentation outline](IS_REVIEW_3_PRESENTATION_OUTLINE.md)
- [Offline incident simulation script](../incident_simulation_ba2018.py)
- [Incident simulation regression tests](../tests/test_incident_simulation_ba2018.py)

## 3. Exact commands for the remaining reproducibility evidence

Run from the repository root in Windows PowerShell with Python 3.12 and the repository's pinned dependencies:

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q -rs
.\.venv\Scripts\python.exe purpose_pfiv_evaluation.py
.\.venv\Scripts\python.exe incident_simulation_ba2018.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_incident_simulation_ba2018.py
~~~

Retain:
- the pytest summary;
- the WPFD/PFIV fixture CSV and summary JSON;
- incident simulation JSON output;
- incident regression test summary;
- latest GitHub Actions run result.

If a command fails, record the actual error and fix it before final submission. Do not insert expected counts into the report as observed outcomes.

## 4. Final team approvals

Before submitting, the team should confirm:
- [ ] British Airways 2018 has not been selected by another team.
- [ ] All report facts follow the ICO penalty notice; attribution is not invented.
- [ ] The Review 1 threat-model mapping matches the submitted Review 1 report.
- [ ] The current repository and README are the versions used to reproduce the results.
- [ ] The incident simulation commands have been run and outputs saved.
- [ ] All team members have verified their individual contribution statements.
- [ ] No actual participant/survey results, live deployment results or real-world security accuracy are fabricated.
- [ ] Final screenshots and diagrams are captured from the actual current system, not illustrative mock-ups.
- [ ] The final report and presentation cite the ICO notice and clearly distinguish offline ML results, controlled PFIV results and exploratory live checks.

## 5. Academic integrity notes

- The British Airways case study is a proposed selection pending the class uniqueness check.
- The Review 1 role allocation is a starting draft, not proof of completed work by each person.
- Existing Review 2 metrics are recorded historical results; the latest repository changes need a fresh test run.
- The incident simulation is synthetic and offline; it is not a reproduction of the actual BA infrastructure or a replay of the real breach.
- The live deployment and demo are intentionally excluded from this checklist and remain a separate task.
