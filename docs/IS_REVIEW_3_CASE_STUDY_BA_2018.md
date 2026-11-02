# IS Review 3 — Real-World Incident Case Study
## British Airways payment-card data breach (2018)

**Project linkage:** PFIV Guard — Website Risk Assessment and Payment Flow Integrity Verification  
**Incident source of record:** UK Information Commissioner's Office (ICO), *British Airways Penalty Notice*, 16 October 2020, case COM0783542.  
**Selection status:** Proposed incident selection. Confirm with the project faculty/team that no other team has selected the same incident before final submission.

---

## 1. Why this incident was selected

The British Airways (BA) incident is closely related to the team's Review 1 threat model because the attacker gained access to BA's systems, changed website JavaScript, and caused a copy of customer payment-card data entered on the genuine BA website to be sent to an attacker-controlled external domain, `BAways.com`. The ordinary booking and payment process continued, so a customer could see an apparently normal checkout while card data was also being copied elsewhere.

This makes the case especially relevant to the Review 1 assets **Payment information** and **Payment-flow integrity**, and to the attack types **Endpoint tampering** and **Redirect/intermediary manipulation**. The ICO's formal notice records the compromise, the malicious JavaScript changes, and the exfiltration destination. It does not publicly identify the attacker, so this report does not attribute the incident to a named threat group.

**Primary source:** [ICO British Airways Penalty Notice (PDF, 16 October 2020)](https://ico.org.uk/media/action-weve-taken/mpns/2618421/ba-penalty-20201016.pdf).

## 2. Incident summary

Between 22 June and 5 September 2018, an attacker used compromised credentials issued to an employee of Swissport, a third-party cargo-services provider, to access BA's remote-access environment. The account was not protected by multi-factor authentication (MFA). The attacker moved beyond the access intended for the third-party user and traversed BA's wider network.

The attacker later located files containing BA website code and modified JavaScript so that a copy of customer card data was sent to `BAways.com`, a domain controlled by the attacker. The skimming was active for 15 days, from 21 August to 5 September 2018. The normal BA booking/payment flow was not visibly interrupted.

On 5 September 2018, a third party informed BA that data was being sent from `britishairways.com` to `BAways.com`. BA contained the malicious code within approximately 90 minutes and blocked the relevant URL paths about 20 minutes later. BA notified the ICO, banks/payment schemes and customers on 6 and 7 September 2018.

The ICO's final notice estimated that personal data of approximately **429,612 individuals** may have been accessed. The categories included:
- 244,000 people: names, addresses, card numbers and CVV numbers;
- 77,000 people: card numbers and CVV numbers;
- 108,000 people: card numbers only;
- BA employee/administrator usernames and passwords; and
- usernames and PINs for up to 612 Executive Club accounts.

On 16 October 2020, the ICO imposed a final penalty of **£20 million**. This is the final penalty amount in the notice, not the earlier proposed penalty.

**Sources:** ICO penalty notice, sections 1, 3.4–3.29, 4.1 and 7; [ICO archived press-release reference](https://www.nationalarchives.gov.uk/).

## 3. Timeline

| Date / period | Incident stage | Evidence-based description |
|---|---|---|
| 22 June 2018 | Initial access | Attacker used compromised Swissport third-party credentials to access BA's Citrix Access Gateway (CAG). |
| June 2018 | Access-control failure | The Swissport account used a single username/password and did not have MFA. |
| June 2018 onward | Lateral movement | The attacker broke out of the intended Citrix access boundary and reached wider BA network resources. |
| 26 July 2018 | Access to stored payment data | The attacker accessed plaintext log files containing card details for BA redemption transactions. |
| 14–25 August 2018 | Website-code modification | The attacker modified website JavaScript to copy/redirect card data to `BAways.com`. |
| 21 August–5 September 2018 | Payment-card skimming | The malicious code remained active for 15 days while normal booking/payment continued. |
| 5 September 2018 | External detection and containment | A third party alerted BA to data being sent to `BAways.com`; BA contained the code and blocked URL paths. |
| 6–7 September 2018 | Notification | BA notified the ICO, banks/payment schemes and affected customers. |
| 16 October 2020 | Regulatory outcome | ICO issued the final £20 million penalty notice. |

**Source:** ICO Penalty Notice, sections 3.4–3.29 and 4.1.

## 4. Root-cause analysis

### 4.1 Technical failures

1. **Weak remote-access authentication.** The compromised third-party account was not protected with MFA. The ICO noted that 13 of 243 applications on the Citrix Access Gateway were not MFA-protected.
2. **Insufficient privilege boundaries.** The attacker moved beyond the intended Swissport access and traversed the wider BA network. The ICO discussed the need for least privilege, application restrictions and stronger controls around the Citrix environment.
3. **Privileged credentials exposed.** The ICO identified plaintext storage of privileged credentials in files and discussed monitoring access to such files and reducing standing administrator privilege.
4. **Sensitive data logged in plaintext.** A test-only logging feature remained enabled in production. Card details, including CVV in many cases, were stored in plaintext from December 2015. The retention period was 95 days.
5. **Website JavaScript integrity was compromised.** The attacker modified JavaScript files associated with the BA website so payment-card data was copied to an external attacker-controlled domain.
6. **Insufficient detection/monitoring.** BA did not identify the attack itself before the third-party notification on 5 September 2018. The ICO discussed security logging and monitoring as important detection controls.

### 4.2 Process and governance failures

1. **Policy implementation gap:** BA's own 2017 Network Access Control Policy required MFA for remote access, including third-party access, but MFA was not consistently applied to all Citrix applications.
2. **Third-party access governance:** Supplier accounts and remote access were not sufficiently constrained to the intended service scope.
3. **Testing coverage:** The ICO criticised the scope/rigour of penetration testing and discussed how more rigorous internal testing could have identified the ability to move from the remote-access environment into the wider network.
4. **Logging configuration and release control:** A test feature that logged sensitive card information was left enabled in production. This points to inadequate production configuration review and data-minimisation controls.
5. **Security monitoring and response:** The breach was first brought to BA's attention by a third party after the skimming had run for 15 days.

**Important distinction:** The formal ICO finding is that BA failed to apply appropriate technical and organisational security measures under GDPR Articles 5(1)(f) and 32. The root-cause categories above summarise specific shortcomings described in the penalty notice; they are not an assertion that one single control failure caused the entire incident.

## 5. Impact

- Approximately 429,612 individuals' personal data was potentially accessed.
- Payment-card data, including CVV for some affected groups, was involved.
- BA employee/administrator credentials and some Executive Club usernames/PINs were also potentially accessed.
- The normal payment process continued, which meant the skimming was not necessarily obvious to customers.
- The incident resulted in regulatory action and a final £20 million ICO penalty in October 2020.

The ICO notice lists potential access, not proof that every listed record was misused. This report therefore uses “potentially accessed” rather than claiming that all records were definitely downloaded or fraudulently used.

---

## 6. Mapping to the team's Review 1 threat model

The Review 1 threat model defines five protected assets: **Credentials; Payment information; Payment-flow integrity; User trust; Banking identity**. It lists attacker capabilities including look-alike domains, cloned pages, modified form actions/client-side endpoints, inserted redirects/iframes/scripts, processor impersonation, HTTPS on malicious domains and distribution through messages/QR codes.

### 6.1 Protected assets

| Review 1 protected asset | Relevance to BA incident | Assessment |
|---|---|---|
| Credentials | Third-party and BA account credentials enabled access; employee/admin credentials were also potentially exposed. | Directly relevant |
| Payment information | Card numbers and CVV were copied to an attacker-controlled domain. | Directly impacted |
| Payment-flow integrity | Customer-facing payment remained functional while an additional data-copy path operated. | Directly impacted |
| User trust | Customers were interacting with the genuine BA website and could reasonably expect their data to remain within the intended payment process. | Directly impacted |
| Banking identity | BA's genuine brand/payment context was abused; however, this was not primarily a cloned-bank identity attack. | Related but not the central attack |

### 6.2 Review 1 attack types

| Review 1 attack type | BA incident mapping | Strength of match |
|---|---|---|
| Credential phishing | Initial compromise involved a third-party credential; the ICO notice does not establish that a phishing website was used to obtain it. | Partial / initial credential compromise; phishing vector unconfirmed |
| Fake payment gateway | BA's genuine payment journey was modified; the ICO notice does not describe a fake gateway impersonating a processor. | Not directly observed |
| Processor impersonation | No evidence in the ICO notice that the attacker claimed one processor while routing to another. | Not observed |
| Endpoint tampering | Website JavaScript was changed so card data was copied to `BAways.com`. | Strong match |
| Redirect/intermediary manipulation | Card data was copied/redirected to an attacker-controlled external domain while normal checkout continued. | Strong match |
| Visual spoofing | The incident did not require a visually cloned page; customers used the genuine BA page. | Not central |
| Domain deception | The attacker-controlled `BAways.com` domain was used as the external destination. | Strong match as a deceptive external domain |
| QR-based redirection | No QR-based attack is described in the official notice. | Not observed |

## 7. Would PFIV Guard have prevented, detected or missed the incident?

PFIV Guard is a user-side, passive inspection prototype. It fetches public HTML and checks visible form actions, observed redirect domains, iframe/script source domains and processor-domain consistency. It does not authenticate internal BA accounts, inspect the compromised BA network, execute browser JavaScript, or observe all runtime browser requests.

Therefore, the following is a reasoned capability assessment—not a claim that PFIV Guard was deployed at BA or could have prevented the historical incident.

| Incident stage | Relevant PFIV Guard capability | Likely outcome | Reason |
|---|---|---|---|
| Swissport credential compromise | URL/HTML, OCR, PFIV | **Miss** | This is an internal identity/remote-access compromise, outside passive inspection of a public checkout URL. |
| MFA gap / initial Citrix access | PFIV / ML | **Miss** | PFIV Guard does not enforce MFA or control BA's remote access gateway. |
| Citrix breakout and lateral movement | URL/HTML / PFIV | **Miss** | The system does not monitor BA's internal network, endpoint telemetry or lateral movement. |
| Plaintext privileged credentials/log files | PFIV | **Miss** | PFIV Guard does not inspect internal credential stores, server logs or access-control configuration. |
| JavaScript tampering inside BA infrastructure | Static HTML / script-host inspection | **Likely miss / partial** | The modified JavaScript was hosted as website code. The current prototype does not compare script hashes against a trusted baseline or execute/semantically inspect JavaScript. |
| Card data copied to `BAways.com` by JavaScript | Payment endpoint / redirect checks | **Likely miss in the actual attack path** | The current implementation extracts HTML form actions, redirects and resource hosts. The historic attack copied data through modified JavaScript while the normal payment journey continued; runtime fetch/XHR/beacon exfiltration is not comprehensively observed. |
| Visible malicious form action to an unexpected domain (counterfactual) | PFIV sensitive form endpoint analysis | **Could detect** | If the attacker had changed the HTML form action to a visible attacker-controlled endpoint, PFIV could classify the unexpected payment destination as Suspicious. |
| Unexpected external script source visible in HTML (counterfactual) | PFIV embedded-resource inspection | **Could flag for review** | The app records script domains and can surface unexpected intermediary-domain evidence. An unexpected script host is a signal to investigate, not proof of malware. |
| Customer notification / regulatory response | PFIV | **Miss** | The prototype is not an incident-response, notification or customer-case-management system. |

**Conclusion:** PFIV Guard is a complementary pre-payment inspection aid. It could provide useful warnings when a sensitive endpoint or unexpected resource is visible in static HTML, but it would not have prevented the initial network compromise or reliably detected the exact JavaScript-based data-copy behaviour documented in the BA incident. This is an important limitation to communicate in Review 3.

## 8. Scaled-down safe simulation

The repository includes a local-only simulation:
- `incident_simulation_ba2018.py`
- `tests/test_incident_simulation_ba2018.py`

Run from the repository root:

```powershell
python incident_simulation_ba2018.py
python -m pytest -q tests/test_incident_simulation_ba2018.py
```

The simulation calls the existing `bankshield_core.analyze_payment_flow` function against synthetic HTML. It uses only the reserved `.example` domain, makes **zero network requests**, submits **zero forms**, and contains no real payment details.

### Simulation cases

| Case | Synthetic fixture | What it tests | Expected PFIV interpretation |
|---|---|---|---|
| S1 — Legitimate control | Stripe-branded page with a visible Stripe endpoint | Positive control | Verified |
| S2 — Visible endpoint diversion | Checkout form action points to `baways.example` | Whether static endpoint tampering is surfaced | Suspicious |
| S3 — External script indicator | Checkout HTML loads script from `baways.example` | Whether an unexpected script host becomes an intermediary-domain review signal | Needs Review |
| S4 — Inline-JavaScript blind spot | Inline script contains a synthetic fetch to `baways.example`; form action remains same-origin | Whether the parser exposes runtime JavaScript exfiltration | Needs Review, but the exfiltration host itself is not extracted |

**Evidence status:** These are designed expected outcomes based on the current code path. Execute the two commands above and retain the actual console/JSON output and test summary before marking the simulation as run. Do not present expected outputs as measured outcomes if the run has not been performed.

### Safe simulation procedure

1. Clone/download the private repository to an authorised team machine.
2. Create a Python 3.12 virtual environment and install `requirements.txt`.
3. From the project root, run the incident simulation script.
4. Run the dedicated pytest file.
5. Save the generated `results/incident_simulations/ba2018_pfiv_simulation_results.json` and the terminal test summary as evidence.
6. Do not replace the synthetic `.example` domain with a real attacker domain. Do not use live BA endpoints, real card data, or a real payment submission.

## 9. Gaps and recommendations

### 9.1 Application-level gaps exposed by the case

1. Static HTML inspection does not reveal every runtime JavaScript `fetch`, `XMLHttpRequest`, `sendBeacon`, dynamically inserted script or client-side data-copy operation.
2. The current application does not maintain a trusted script-hash baseline or detect unexpected code changes in a first-party script.
3. A legitimate domain and a valid TLS certificate do not prove that its JavaScript or payment flow is uncompromised.
4. PFIV Guard does not monitor remote-access identities, MFA coverage, privileged account usage, server logs, application deployment pipelines or internal lateral movement.
5. Processor-domain registry matching is finite and does not prove the safety of every loaded script or payment provider.
6. The current four-case PFIV validation is a logic check on controlled fixtures, not a broad real-world incident dataset.

### 9.2 Recommendations

| Priority | Recommendation | Why it matters |
|---|---|---|
| Critical | Enforce MFA for every remote and third-party access path; use conditional access and IP restrictions where appropriate. | Reduces the chance that one stolen password gives network access. |
| Critical | Apply least privilege, strong network segmentation and strict application allowlisting for supplier access. | Limits lateral movement after account compromise. |
| Critical | Remove sensitive card data and CVV from logs; prevent test-only logging in production; minimise retention. | Reduces stored-data exposure. |
| High | Protect website JavaScript with Content Security Policy (CSP), Subresource Integrity (SRI) where applicable, strict script allowlists and change control. | Reduces unauthorised script substitution and limits script execution paths. |
| High | Monitor client-side payment-page scripts and browser network requests for unexpected exfiltration destinations. | Addresses attacks that preserve the normal form action but copy data through JavaScript. |
| High | Centralise security logs and alert on unusual administrator creation, privileged-file access, remote login patterns and unexpected outbound destinations. | Improves detection and investigation time. |
| High | Run regular external and internal penetration tests, including a scenario where a third-party account is compromised. | Tests trust boundaries and lateral movement assumptions. |
| Medium | Maintain a supplier inventory, access review, contractual security requirements and offboarding process. | Improves third-party governance. |
| Medium | Add a runtime-observation research branch to PFIV Guard, clearly separating static findings from browser-observed network events. | Improves coverage while preserving evidence transparency. |
| Medium | Expand the PFIV evaluation corpus and report precision, recall, false positives and false negatives on independent labelled cases. | Establishes measurable effectiveness beyond four fixtures. |

## 10. Conclusion

The British Airways incident demonstrates that payment security cannot be assessed solely by the visual legitimacy of a checkout page or by the apparent success of the normal payment flow. A genuine page can be compromised so that payment data is copied through an additional JavaScript-driven path.

PFIV Guard's focus on visible sensitive endpoints, processor consistency and unexpected intermediary domains is relevant to this class of risk. However, the BA incident also demonstrates the need for runtime browser monitoring, script integrity controls, identity security, network segmentation and server-side monitoring. The project should therefore be presented as a **complementary defensive inspection prototype**, not as a replacement for enterprise security controls and not as a tool that would certainly have prevented the BA breach.

---

## References

1. Information Commissioner's Office (ICO), *British Airways Penalty Notice*, case COM0783542, 16 October 2020. [Official PDF](https://ico.org.uk/media/action-weve-taken/mpns/2618421/ba-penalty-20201016.pdf).
2. UK Information Commissioner's Office, Annual Report 2020/21, noting the £20 million BA penalty and the fact that the attack was not detected by BA for more than two months. [Official report (PDF)](https://ico.org.uk/media2/migrated/2620166/hc-354-information-commissioners-ara-2020-21.pdf).
3. RiskIQ, *Magecart British Airways Breach* (technical analysis of the web skimming code). [RiskIQ Labs](https://www.riskiq.com/blog/labs/magecart-british-airways-breach/).
4. UK Government, *Cyber Primer*, case study on theft of personal data — British Airways. [Official PDF](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/549291/20160720-Cyber_Primer_ed_2_secured.pdf).

**Source hierarchy:** The ICO penalty notice is the authoritative source for the formal incident chronology, findings, affected-data categories and final penalty. RiskIQ is supplementary technical analysis. Where secondary accounts differ on technical details or attribution, this report follows the ICO notice and does not assign a named attacker.
