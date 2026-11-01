"""Transparent weighted evidence fusion used by the BankShield prototype."""
from urllib.parse import urlsplit


def url_risk_score(url: str, page: dict):
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    score = 0.0
    reasons = []
    if parsed.scheme.lower() != "https":
        score += 25
        reasons.append("The URL does not use HTTPS.")
    if len(url) > 100:
        score += 10
        reasons.append("The URL is unusually long.")
    if "@" in url:
        score += 15
        reasons.append("The URL contains '@', which can obscure the destination.")
    if host.count(".") >= 4:
        score += 10
        reasons.append("The URL contains many subdomain levels.")
    words = ["verify", "secure", "login", "update", "confirm", "account", "payment", "banking"]
    hits = [word for word in words if word in host.lower()]
    if len(hits) >= 2:
        score += 10
        reasons.append("The domain contains multiple security/payment-related keywords.")
    if page.get("payment_page_detected"):
        reasons.append("Payment/checkout characteristics were detected.")
    return min(score, 100), reasons


def fuse_evidence(
    url_score,
    visual_score=None,
    payment_score=None,
    threat_score=None,
    ml_score=None,
    payment_status="Not Applicable",
):
    """Fuse available risk scores. None means that evidence branch was unavailable/not provided.

    Weights are normalized over supplied branches. A zero score means the branch was
    evaluated and did not produce a risk signal; None means the branch did not run.
    """
    weights = {
        "url": (0.25, url_score),
        "visual": (0.10, visual_score),
        "payment": (0.30, payment_score),
        "threat": (0.10, threat_score),
        "ml": (0.25, ml_score),
    }
    numerator = 0.0
    denominator = 0.0
    for weight, value in weights.values():
        if value is None:
            continue
        value = max(0.0, min(100.0, float(value)))
        numerator += weight * value
        denominator += weight
    final_score = numerator / denominator if denominator else 50.0
    final_score = max(0.0, min(100.0, final_score))

    # Conservative PFIV policy: a clearly suspicious data path cannot be cancelled
    # by lower scores from unrelated evidence branches.
    if payment_status == "Suspicious":
        final_score = max(final_score, 65.0)
        label = "High Risk"
    elif payment_status == "Needs Review":
        final_score = max(final_score, 40.0)
        label = "High Risk" if final_score >= 65 else "Suspicious"
    elif payment_status == "Unverifiable":
        final_score = max(final_score, 35.0)
        label = "High Risk" if final_score >= 65 else "Suspicious"
    else:
        if final_score >= 65:
            label = "High Risk"
        elif final_score >= 35:
            label = "Suspicious"
        else:
            label = "Legitimate"

    # A strong screenshot/OCR pressure indicator should not be diluted into a
    # reassuring label by lower URL/ML signals. This only raises to Suspicious;
    # the OCR score is heuristic and is not treated as a calibrated probability.
    if visual_score is not None and float(visual_score) >= 45:
        final_score = max(final_score, 40.0)
        if final_score >= 65:
            label = "High Risk"
        else:
            label = "Suspicious"

    return {"score": round(final_score, 2), "label": label}
