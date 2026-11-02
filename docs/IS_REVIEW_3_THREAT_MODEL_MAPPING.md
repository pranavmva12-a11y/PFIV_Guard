# IS Review 3 — Review 1 Threat Model Mapping to the British Airways 2018 Incident

**Project:** PFIV Guard  
**Incident:** British Airways payment-card data breach, 2018  
**Primary incident source:** UK ICO, British Airways Penalty Notice, 16 October 2020.

## 1. Scope of this mapping

This document maps the attack described in the ICO's British Airways penalty notice to the assets, attacker capabilities and attack types already defined in the team's Review 1 threat model.

The mapping is a retrospective capability analysis. PFIV Guard was not deployed by British Airways, and this document does not claim that the prototype would have prevented the historical incident. It identifies what the current implementation can inspect, what it would likely miss, and what controls sit outside its scope.

## 2. Review 1 protected assets

| ID | Protected asset from Review 1 | Incident relevance |
|---|---|---|
| A1 | Credentials — usernames, passwords, OTP-related prompts | Compromised third-party account enabled initial access; BA employee/admin credentials were also potentially exposed. |
| A2 | Payment information — card fields, CVV, account/payment details | Card information was copied to an attacker-controlled domain. |
| A3 | Payment-flow integrity — form actions, processor domains, redirects | The legitimate checkout continued while an additional JavaScript-driven data-copy path operated. |
| A4 | User trust — clarity of the security assessment | Customers used the genuine BA website and could be unaware that card data was being copied. |
| A5 | Banking identity — bank/merchant and processor context | BA's genuine merchant identity and payment context were abused; this was not principally a fake-bank clone. |

## 3. Review 1 attacker capabilities

| ID | Attacker capability from Review 1 | Seen in BA incident? | Evidence interpretation |
|---|---|---|---|
| C1 | Register/control look-alike domains and subdomains | Related | The attacker used BAways.com as an external collection destination. The ICO notice describes it as attacker-controlled; this is not the same as a complete look-alike bank domain. |
| C2 | Clone the appearance, wording and structure of a genuine page | No evidence in notice | The customer used the genuine BA site; the attack did not depend on a cloned checkout. |
| C3 | Modify form actions or client-side endpoints | Related / strong | The malicious JavaScript caused card data to be copied to BAways.com. The public notice describes JavaScript manipulation; do not state that the HTML form action itself was necessarily modified. |
| C4 | Insert redirects, iframes, scripts or intermediate domains | Strong | JavaScript and an attacker-controlled external destination were involved in the additional data path. |
| C5 | Imitate a known processor's name or branding | Not established | The ICO notice does not say the attacker impersonated a processor. |
| C6 | Use HTTPS on a malicious domain | Not established in official notice | Do not claim this happened in this incident without independent evidence. |
| C7 | Distribute malicious URLs through messages, social media, email or QR codes | Not established | Initial access was through compromised third-party credentials, not a documented QR/social phishing delivery vector. |

## 4. Review 1 attack-type mapping

| Review 1 attack type | BA incident mapping | Match |
|---|---|---|
| Credential phishing | Third-party credentials were compromised, but the ICO notice does not establish how they were stolen. | Partial; phishing vector unconfirmed |
| Fake payment gateway | BA's genuine payment journey was modified; no fake gateway is described. | Not directly observed |
| Processor impersonation | No evidence of processor-brand impersonation or a false processor claim. | Not observed |
| Endpoint tampering | Website JavaScript was changed to copy payment-card data to BAways.com. | Strongly related |
| Redirect/intermediary manipulation | An additional external data-copy path to BAways.com was introduced while normal payment processing continued. | Strongly related |
| Visual spoofing | No cloned visual interface was required. | Not central |
| Domain deception | Attacker-controlled BAways.com was the external destination. | Related |
| QR-based redirection | No QR-based redirection is described. | Not observed |

## 5. Attack-stage mapping: system outcome

Outcome definitions:
- **Could detect:** the relevant indicator is within the current prototype's observable static HTML/page evidence, assuming it is present and successfully fetched.
- **Partial / review signal:** some supporting signal is visible, but it is not proof of an active malicious behavior.
- **Likely miss:** the event is outside the current application's data source or analysis capability.
- **Prevent:** reserved for a control that can block the relevant action. PFIV Guard is passive and does not enforce BA infrastructure access controls, so it should not be credited with preventing the historical initial compromise.

| BA incident stage | Review 1 asset / threat | PFIV Guard capability | Assessment |
|---|---|---|---|
| Third-party account compromise | A1 Credentials; credential compromise | No identity-provider or account telemetry | Likely miss |
| Third-party remote access without MFA | A1 Credentials; weak authentication | No MFA enforcement or remote-access monitoring | Miss |
| Citrix breakout and lateral movement | A1 Credentials; privilege boundary failure | No internal network or endpoint monitoring | Miss |
| Access to privileged plaintext credentials and stored logs | A1/A2 Credentials and payment information | No internal file, credential vault or server-log inspection | Miss |
| Website JavaScript modification | A2/A3 Payment information and flow integrity; C3/C4 endpoint/script tampering | Static page and external-resource inspection; no trusted script hash baseline | Partial at best; likely miss if the changed script is served from the legitimate first-party origin |
| JavaScript copies card data to BAways.com at runtime | A2/A3; C3/C4 | Parses static HTML form actions, script src, iframes and redirect chain; does not execute JS or observe all runtime network requests | Likely miss for the documented JS-driven data-copy path |
| Counterfactual: HTML form action visibly points to BAways.com | A2/A3; endpoint tampering | Extracts sensitive payment form action and endpoint domain | Could detect and classify Suspicious |
| Counterfactual: external script src visibly points to BAways.com | A2/A3; external script/intermediary | Extracts static script source domains and intermediary-domain evidence | Partial / Needs Review; host anomaly is not proof of malware |
| Third-party alert and BA response | A4 User trust; incident response | No SOC, alert triage or customer notification workflow | Miss |

## 6. Prevent / detect / miss summary

| Capability category | What can honestly be claimed |
|---|---|
| Prevent | PFIV Guard does not prevent the initial credential compromise, MFA gap, Citrix breakout, internal lateral movement or server-side JavaScript modification. It is a passive inspection prototype and does not enforce access controls. |
| Detect | It can detect a visible unexpected sensitive form endpoint in static HTML; it can also surface unexpected external script/resource domains for review. |
| Partial | It may provide a generic payment-flow review state if payment-page structure is visible, but that does not mean it found the runtime exfiltration destination. |
| Miss | It does not detect the Swissport credential compromise, internal privilege escalation, stored plaintext log files, internal server-code change or every runtime JavaScript exfiltration. |

**Key conclusion:** PFIV Guard addresses one subset of the incident's observable payment-page risk. It is a complementary user-side inspection aid, not a substitute for MFA, least privilege, network segmentation, script integrity management, centralised monitoring or incident response.

## 7. Safe, scaled-down test scenarios

The repository's new offline simulation uses synthetic pages and the reserved .example domain. It does not contact the real BA website, BAways.com, payment processors or any external host.

| Test ID | Test fixture | Objective | Evidence to retain |
|---|---|---|---|
| S1 | Legitimate Stripe form endpoint | Positive control; known processor path | JSON output showing processor, consistency and PFIV state |
| S2 | Checkout form action points to baways.example | Test visible sensitive-endpoint diversion | JSON output showing external endpoint and Suspicious state |
| S3 | External script src points to baways.example | Test static third-party script-domain review signal | JSON output showing script domain and Needs Review state |
| S4 | Inline JS contains a synthetic fetch to baways.example while form action remains same-origin | Demonstrate that runtime exfiltration in inline JS is not extracted by static PFIV | JSON output: generic state/evidence and absence of baways.example from extracted script domains |

### Run from repository root

~~~powershell
python incident_simulation_ba2018.py
python -m pytest -q tests/test_incident_simulation_ba2018.py
~~~

The simulation script creates:
- results/incident_simulations/ba2018_pfiv_simulation_results.json

Before the run, the expected outcomes are hypotheses based on the current code, not measured results. Save the actual terminal output and generated JSON. If an outcome differs, report the observed result and investigate the code rather than editing the report to the expected value.

## 8. What the simulation proves — and does not prove

It can demonstrate that:
- a visible unexpected sensitive payment form endpoint can be identified by the existing PFIV logic;
- an unexpected external script host may become intermediary-domain evidence;
- an inline JavaScript destination is not currently extracted by the static parser; and
- the app's uncertainty state is important when the entire path cannot be verified.

It does not demonstrate that:
- the historical BA attack has been recreated;
- PFIV Guard would have stopped the attacker from entering BA's network;
- the exact historical script behavior is fully simulated;
- every third-party script is malicious;
- all payment skimmers can be detected; or
- the four controlled cases measure real-world detection accuracy.

## 9. Recommendations derived from the mapping

1. Enforce MFA on all third-party and remote-access paths.
2. Restrict third-party accounts through least privilege, application allowlisting, segmentation and time-bound access.
3. Remove card data and CVV from logs; enforce production configuration checks and retention limits.
4. Protect payment-page JavaScript with change control, script integrity controls and strict CSP/SRI where applicable.
5. Monitor runtime payment-page network traffic for unexpected data destinations and newly inserted scripts.
6. Centralise security logging and alert on unusual privileged-file access, admin activity and unexpected outbound traffic.
7. Expand PFIV Guard with a clearly separated browser-observed runtime evidence mode; do not label static checks as runtime verification.
8. Evaluate the expanded system with a larger labelled corpus and independent tests.

## 10. Authoritative incident source

UK Information Commissioner's Office (ICO), *British Airways Penalty Notice*, case COM0783542, 16 October 2020:
https://ico.org.uk/media/action-weve-taken/mpns/2618421/ba-penalty-20201016.pdf

The ICO notice is the primary source for the formal timeline, technical findings, affected data categories and final penalty. The notice does not identify the attacker by name or state that a phishing message or QR code was the initial credential theft method. This mapping therefore avoids attributing those unproven details to the incident.
