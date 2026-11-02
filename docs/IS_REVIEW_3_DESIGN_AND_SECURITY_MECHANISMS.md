# IS Review 3 — Design Choices and Security Mechanisms

**Project:** PFIV Guard (formerly BankShield AI)  
**Core focus:** Payment Flow Integrity Verification (PFIV)

## 1. Design objective

PFIV Guard is a defensive research prototype for inspecting the visible structure and observable indicators of public banking, e-commerce and checkout pages. Its design addresses a specific security question:

> Does the inspected page's observable sensitive-payment path appear consistent with the payment processor and context represented by the page, and are unexpected endpoints or intermediary domains visible?

The system is designed for passive inspection. It does not submit forms, enter credentials, process card information or initiate QR/UPI payments.

## 2. Architecture and key design decisions

| Design choice | Current implementation | Security/research rationale |
|---|---|---|
| Separate page purpose from transaction intent | Website Purpose & Functionality Detection (WPFD) produces a page category and evidence strength; transaction-intent logic separately determines whether PFIV is applicable. | A payment company's marketing homepage should not automatically be treated as an active checkout. |
| Run PFIV only when transaction intent is detected | The shared analysis pipeline uses purpose/transaction evidence to decide whether payment-flow inspection is relevant. | Reduces irrelevant payment checks on informational, login-only or marketing pages. |
| Treat uncertainty explicitly | PFIV may return Verified, Suspicious, Needs Review or Unverifiable; non-payment pages use Not Applicable. | Missing evidence is not equivalent to phishing. |
| Inspect the sensitive submission path | Extracts payment-specific forms and their action destinations. | Focuses on where payment information is intended to go, not only page appearance. |
| Compare processor context | Uses a finite processor-domain registry to identify known processors and compare page claims with observed domains. | Detects certain processor mismatches; registry limitations are disclosed. |
| Inspect redirects and embedded resources | Records redirect chain, iframe domains and external script domains. | Exposes some unexpected intermediary and resource signals in static HTML. |
| Fuse multiple evidence branches | URL/HTML ML, OCR heuristic and applicable PFIV evidence contribute to transparent weighted fusion. | Avoids relying on one signal; weights remain fixed and understandable. |
| Explain ML evidence | Random Forest results and SHAP/feature-importance outputs are exposed in the interface. | Makes the URL/HTML model's feature contributions more inspectable. |
| Keep screenshot and QR inputs as evidence sources | Screenshot OCR extracts text/URLs; QR decoder displays URL or UPI payload fields. | Adds input coverage without claiming a trained screenshot classifier or UPI payee authentication. |
| Use controlled fixtures for sensitive scenarios | Synthetic local HTML pages exercise the PFIV states without real credentials or payments. | Allows repeatable defensive tests without interacting with real payment systems. |

## 3. Security mechanisms implemented

| Mechanism | Current code behavior | Threat/impact addressed | Remaining limitation |
|---|---|---|---|
| URL normalization and validation | Normalizes scheme/host; rejects unsupported schemes, embedded credentials, invalid ports, control whitespace and oversized URLs. | Reduces malformed URL handling and unsupported protocol abuse. | Input validation alone does not authenticate a site. |
| HTTP/HTTPS-only fetching | Rejects non-web schemes such as file/data/javascript. | Prevents unintended protocol handlers from being used as fetch targets. | Only the implemented fetch path is covered. |
| Local/private destination blocking | Blocks localhost/internal hostnames and private, loopback, link-local and reserved IP addresses by default. | Reduces server-side request forgery (SSRF) exposure to local services and private networks. | No independent penetration test or DNS-rebinding assessment has been completed. |
| DNS resolution checks | Resolves hostnames and rejects non-global IP results before requests. | Reduces risk from domains resolving to private/reserved IPs. | DNS/time-of-check/time-of-use and rebinding risks require further specialist assessment. |
| Redirect revalidation | Disables automatic redirects, follows them manually, revalidates each destination and caps redirect hops at five. | Reduces redirect-based bypass of destination checks and excessive redirect chains. | It does not provide complete browser navigation/runtime redirect visibility. |
| Request timeouts | Uses 5-second connect and 10-second read timeouts. | Reduces indefinite connection/read waits. | Network/runtime performance remains variable. |
| Response-size bound | Inspects up to 2 MB of response content. | Limits resource consumption from oversized pages. | Later content may be omitted; truncated pages can produce incomplete findings. |
| User-agent and HTML-only request preference | Sends a defensive research user-agent and requests HTML/XHTML. | Limits fetch purpose to page inspection. | Websites may return different content, require JavaScript or block automated clients. |
| Per-session analysis limit | Allows up to 12 analysis requests in a 10-minute browser session. | Provides a basic demo abuse guard. | This is not global rate limiting or protection against coordinated abuse. |
| Local fixture bypass hidden by default | Local demo control is rendered only when the operator explicitly sets the local development environment variable; disabled by default. | Prevents exposing the local fixture exception in the normal hosted UI. | Public deployment must not set this environment variable. |
| Passive payment inspection | Extracts form metadata and destinations but does not submit forms. | Avoids sending card or credential values to inspected websites. | Does not prove the destination is safe or reveal runtime behavior after user interaction. |
| No real payment data collection | Project workflow does not request or store actual card numbers, CVV, OTP, PIN or bank passwords. | Reduces sensitive-data handling risk during demonstration. | Team demonstrations must continue using synthetic data only. |
| QR/UPI non-transaction design | Decodes and displays payload fields; does not launch payment apps or submit transactions. | Avoids unintended payments. | Decoding does not authenticate the UPI payee or QR owner. |

## 4. Payment-flow detection logic

The current PFIV code distinguishes:
- payment-specific fields (for example, card number, CVV, expiry, UPI and bank-account details);
- credential fields (for example, username, password, OTP and PIN);
- observed processor domains;
- external sensitive form destinations;
- page claims about processors;
- redirect domains;
- iframe and external script domains.

A generic username/password form is not by itself a payment flow. The implementation aims to avoid treating ordinary login pages as active payment pages.

A processor visible in a script or iframe is not automatically sufficient to mark the sensitive payment path Verified. The current logic requires stronger evidence, including a known processor endpoint and consistency with the page's processor claim, with no unexpected intermediary domains.

## 5. Security design coverage against Review 1

| Review 1 threat | Relevant mechanism | Coverage |
|---|---|---|
| Fake payment gateway | Payment-page detection, payment form extraction, processor context | Partial; static page only |
| Processor impersonation / mismatch | Processor claim and observed-domain comparison | Partial; depends on registry and visible page evidence |
| Endpoint tampering | Sensitive form-action extraction and unexpected external endpoint checks | Good for visible static form actions |
| Redirect/intermediary manipulation | Manual redirect chain and intermediary-domain checks | Partial; does not observe all browser runtime requests |
| Domain deception | URL/host feature analysis and page fetch validation | Partial; no complete identity proof |
| Visual spoofing | Screenshot OCR and URL extraction | Limited; no trained visual/logo classifier |
| QR-based redirection | QR decode and optional URL analysis | Partial; does not verify recipient/payee identity |
| Credential phishing | URL/HTML and OCR evidence | Partial; not a credential protection gateway |
| Internal account compromise / lateral movement | None | Out of scope |

## 6. Important controls not implemented

The following controls are not currently part of the working prototype and must not be claimed as implemented:
- MFA or identity-provider enforcement;
- endpoint detection and response (EDR);
- internal network segmentation or firewall policy enforcement;
- secure software supply-chain attestation;
- trusted script-hash baselining or automatic JavaScript integrity monitoring;
- full browser execution and runtime network monitoring;
- live VirusTotal, PhishTank or OpenPhish feed validation in the recorded quantitative experiment;
- production-grade central rate limiting, abuse monitoring or SOC alerting;
- independent SSRF penetration testing.

## 7. Threat-informed improvements

The British Airways 2018 incident highlights that a payment page may continue to function while additional JavaScript copies data to an unexpected destination. To improve PFIV Guard, the most relevant next steps are:

1. Add a browser-observed runtime evidence mode to inspect fetch/XHR/sendBeacon destinations and dynamically inserted resources on controlled pages.
2. Add optional script-integrity evidence, with trusted baselines and explicit caveats for legitimate third-party changes.
3. Display static HTML evidence and runtime-observed evidence as separate categories.
4. Add stronger provenance and update policy for the processor registry.
5. Expand the fixture suite to include inline scripts, dynamically loaded scripts, iframes, redirects, same-origin endpoints and legitimate third-party processor assets.
6. Perform independent SSRF and DNS-rebinding testing before any production use.
7. Preserve the prototype's safety constraints: no credential submission and no real payment data.

## 8. Conclusion

The current design combines URL/HTML phishing evidence with a purpose-aware PFIV branch and supporting screenshot/OCR and QR analysis. Its strongest implemented protections are passive page inspection, destination validation for server-side fetches, visible payment-form endpoint inspection, processor-consistency checks and explicit uncertainty states. Its most important limitation is that it does not execute or monitor the browser's complete runtime JavaScript/network behavior. It should therefore be presented as an academic defensive inspection prototype that complements—not replaces—identity security, network controls, script integrity management and enterprise monitoring.

## 9. Source files

- app.py — Streamlit UI and request-session limit.
- bankshield_core.py — URL validation, SSRF-oriented fetch checks, redirect handling, page parsing and PFIV.
- analysis_pipeline.py — shared purpose-aware analysis pipeline.
- website_purpose.py — WPFD and transaction-intent heuristics.
- fusion.py — evidence fusion.
- live_ml.py — live feature adapter and Random Forest inference.
- visual_branch.py — screenshot/OCR branch.
- qr_branch.py — QR/UPI decoding branch.
- data/processors.json — finite processor reference registry.
- docs/IS_REVIEW_3_CASE_STUDY_BA_2018.md — incident linkage and security recommendations.
