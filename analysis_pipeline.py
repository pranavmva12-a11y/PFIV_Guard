"""Shared URL analysis pipeline used by URL, screenshot and QR input modes."""
from __future__ import annotations

import time

from bankshield_core import fetch_page, analyze_payment_flow, extract_page_data, normalize_url
from fusion import url_risk_score, fuse_evidence
from live_ml import predict_live_url
from website_purpose import classify_website_purpose, detect_transaction_intent


def analyze_page_security_context(response, html: str) -> tuple[dict, dict, dict]:
    """Return (website purpose, transaction intent, purpose-gated PFIV result).

    The lightweight page parser extracts form and content signals first.
    The PFIV scoring/processor-analysis function is called only when the
    transaction-intent gate identifies an active transaction step.
    """
    website_purpose = classify_website_purpose(response, html)
    page_data = extract_page_data(response, html)
    transaction_intent = detect_transaction_intent(response, html, page_data)

    if transaction_intent["is_transaction_page"]:
        # Do the full payment-flow inspection only for an indicated transaction.
        payment = analyze_payment_flow(response, html)
    else:
        # Retain the raw page keyword signal for diagnostics, but prevent it
        # from affecting URL-risk scoring or implying a payment transaction.
        page_data["raw_payment_keyword_detection"] = bool(page_data.get("payment_page_detected"))
        page_data["payment_page_detected"] = False
        payment = {
            "status": "Not Applicable",
            "score": 0,
            "evidence": [
                transaction_intent["reason"] + " PFIV scoring and processor-path inspection were not run for this page."
            ],
            "page": page_data,
            "processor": None,
            "processor_hits": {},
            "processor_consistency": "Not applicable",
            "external_endpoints": [],
            "intermediate_domains": [],
            "redirect_chain": [],
        }

    payment["transaction_intent"] = transaction_intent
    payment["applicability"] = "Applicable" if transaction_intent["is_transaction_page"] else "Not Applicable"
    return website_purpose, transaction_intent, payment


def analyze_url_input(url: str, *, visual_score: float | None = None, allow_local_fixture: bool = False) -> dict:
    """Run shared website-purpose + URL/HTML + ML + PFIV + evidence fusion.

    visual_score should only be supplied when a screenshot was actually analysed.
    Threat intelligence is marked unavailable rather than reported as zero risk.
    """
    total_start = time.perf_counter()
    response, html = fetch_page(url, allow_local_fixture=allow_local_fixture)
    fetched = time.perf_counter()
    content_type = (response.headers.get("Content-Type") or "").lower()
    is_html = ("text/html" in content_type) or ("application/xhtml+xml" in content_type) or not content_type
    if not is_html:
        raise ValueError(
            f"The destination returned '{content_type}', not an HTML page. "
            "The URL and QR payload can still be inspected separately, but this response is not supported by the HTML pipeline."
        )

    website_purpose, transaction_intent, payment = analyze_page_security_context(response, html)
    page = payment["page"]
    pfiv_done = time.perf_counter()
    url_score, url_reasons = url_risk_score(response.url, page)

    ml_error = None
    try:
        live_ml = predict_live_url(normalize_url(url), response, html)
        ml_score = float(live_ml["phishing_probability"]) * 100.0
        ml_available = True
    except Exception as exc:
        live_ml = {"prediction": None, "label": "Unavailable", "phishing_probability": None, "features": {}}
        ml_score = None
        ml_available = False
        ml_error = f"Live ML inference unavailable: {type(exc).__name__}: {exc}"

    ml_done = time.perf_counter()
    payment_score = None if payment["status"] == "Not Applicable" else float(payment["score"])
    fusion = fuse_evidence(
        url_score=url_score,
        visual_score=visual_score,
        payment_score=payment_score,
        threat_score=None,  # live external threat-intelligence feed is not active
        ml_score=ml_score,
        payment_status=payment["status"],
    )
    total_done = time.perf_counter()

    evidence = list(url_reasons) + list(payment["evidence"])
    evidence.extend(website_purpose.get("evidence", []))
    if ml_error:
        evidence.append(ml_error)
    if response.status_code >= 400:
        evidence.append(f"The server returned HTTP status {response.status_code}; this may limit the available page evidence.")
    if response.headers.get("X-BankShield-Content-Truncated") == "true":
        evidence.append("The response was truncated at the configured size limit; some page content may not have been analysed.")
    if visual_score is not None:
        evidence.append(f"Screenshot/OCR heuristic score included in fusion: {visual_score:.1f}/100. This is an indicator score, not a calibrated phishing probability.")

    return {
        "input_url": url,
        "normalized_url": response.url,
        "http_status": response.status_code,
        "content_type": content_type or "not provided by server",
        "page_title": page.get("title", ""),
        "website_purpose": website_purpose,
        "transaction_intent": transaction_intent,
        "payment": payment,
        "live_ml": live_ml,
        "ml_available": ml_available,
        "ml_error": ml_error,
        "ml_score": ml_score,
        "url_score": url_score,
        "url_reasons": url_reasons,
        "visual_score": visual_score,
        "threat_intelligence": "Not connected in this version",
        "fusion": fusion,
        "evidence": evidence,
        "timings": {
            "fetch_seconds": round(fetched - total_start, 4),
            "pfiv_seconds": round(pfiv_done - fetched, 4),
            "ml_seconds": round(ml_done - pfiv_done, 4),
            "total_seconds": round(total_done - total_start, 4),
        },
        "limitations": [
            "Live Random Forest features are approximations of the UCI benchmark features; not all 30 source features can be obtained from every live website.",
            "Payment-flow inspection reads observable HTML form actions and resource/redirect metadata; it does not observe every browser runtime request.",
            "Live external threat-intelligence feeds are not connected in this build.",
            "Website-purpose and transaction-intent labels are explainable static-HTML heuristics; they do not authenticate the website owner or prove the site's real-world business identity.",
            "Dynamic JavaScript-rendered controls and browser runtime network activity may not be visible to the static HTML purpose/PFIV inspection.",
        ],
    }
