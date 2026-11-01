"""Explainable website-purpose and transaction-intent heuristics for PFIV Guard.

This module classifies the purpose of the *inspected page* from static HTML
signals. It is not a brand-authentication service and it does not prove that a
website is legitimate. Transaction intent is evaluated separately so a
payment-company marketing homepage is not mistaken for an active checkout page.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup


CATEGORY_LABELS = {
    "informational": "Informational / Knowledge",
    "ecommerce": "E-commerce / Shopping",
    "banking": "Banking / Financial Services",
    "payment_gateway": "Payment Gateway / FinTech",
    "booking": "Booking / Reservations",
    "productivity": "Productivity / SaaS",
    "education": "Education / Learning",
    "news": "News / Media",
    "government": "Government / Public Services",
    "healthcare": "Healthcare / Medical Services",
    "other": "Other / General Website",
    "unknown": "Unknown / Insufficient Evidence",
}

# Each phrase is page-purpose evidence, not a trust or reputation signal.
CATEGORY_RULES = {
    "payment_gateway": [
        "payment gateway", "payment processing", "accept payments", "online payments",
        "merchant payments", "payment links", "payment platform", "payment infrastructure",
        "payment orchestration", "payouts platform",
    ],
    "banking": [
        "online banking", "internet banking", "net banking", "mobile banking",
        "bank account", "savings account", "current account", "fund transfer",
        "money transfer", "banking services", "financial services", "personal loan",
        "business banking", "bank login",
    ],
    "ecommerce": [
        "e-commerce", "ecommerce", "online shopping", "shopping cart", "add to cart",
        "shop now", "product catalogue", "product catalog", "buy now", "place order",
        "order history", "my orders", "online store", "cart",
    ],
    "booking": [
        "ticket booking", "flight booking", "hotel booking", "train booking",
        "book tickets", "book now", "make a reservation", "reservation", "appointments",
        "travel booking", "seat availability", "check availability",
    ],
    "productivity": [
        "productivity", "project management", "team workspace", "online documents",
        "spreadsheet", "cloud storage", "collaboration workspace", "customer relationship management",
        "crm software", "business software", "work management", "workspace",
    ],
    "education": [
        "online learning", "learning platform", "online courses", "university",
        "school", "education", "course catalogue", "course catalog", "student portal",
        "learning management system", "tutorials", "training courses",
    ],
    "news": [
        "latest news", "breaking news", "news headlines", "news website", "newspaper",
        "news and media", "journalism", "world news", "live news",
    ],
    "government": [
        "government services", "public services", "citizen services", "official portal",
        "government portal", "govt services", "tax services", "public information",
    ],
    "healthcare": [
        "healthcare", "health services", "hospital", "clinic", "medical services",
        "doctor appointment", "patient portal", "find a doctor", "medical centre", "medical center",
    ],
    "informational": [
        "encyclopedia", "knowledge base", "reference information", "documentation",
        "technical documentation", "research articles", "articles and guides", "wiki",
        "learn more", "information resource", "frequently asked questions",
    ],
}

# Strong cues imply that the inspected page itself may be in a transaction step.
# Generic wording such as "we accept payments" is deliberately not sufficient.
TRANSACTION_CUES = [
    "checkout", "check out", "pay now", "pay securely", "complete payment",
    "proceed to payment", "payment details", "payment method", "card number",
    "credit card", "debit card", "cvv", "cvc", "expiry date", "billing address",
    "billing details", "place order", "confirm order", "order summary", "order total",
    "amount due", "upi id", "enter upi", "scan and pay", "pay bill", "bill payment",
    "transfer funds", "send money", "confirm and pay", "complete your purchase",
]
GENERIC_PAYMENT_CUES = [
    "payment", "payments", "pay", "payout", "payouts", "billing", "transaction", "transactions",
]

PAYMENT_FIELD_CUES = [
    "card_number", "cardnumber", "credit_card", "debit_card", "card number",
    "cvv", "cvc", "expiry", "expiration", "upi", "iban", "swift",
    "routing_number", "bank_account_number", "account_number",
]


# Exact action labels are inspected on controls, not matched anywhere in marketing copy.
ACTIVE_PAYMENT_ACTIONS = [
    "pay now", "pay securely", "confirm and pay", "complete payment",
    "proceed to payment", "submit payment", "pay bill", "transfer now",
    "send money now",
]
ACTIVE_TRANSACTION_CONTEXT = [
    "card number", "card details", "credit card", "debit card", "cvv", "cvc",
    "expiry date", "payment method", "payment details", "billing address",
    "billing details", "order summary", "order total", "amount due",
    "confirm order", "place order",
]
CHECKOUT_PATH_SEGMENTS = {
    "checkout", "payment", "billing", "purchase", "order-review",
    "order-confirmation", "confirm-order", "pay",
}


def _has_phrase(text: str, phrase: str) -> bool:
    text = (text or "").lower()
    phrase = phrase.lower()
    if " " in phrase or "-" in phrase or "_" in phrase:
        return phrase in text
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text) is not None


def _matches(text: str, phrases: list[str]) -> list[str]:
    return [phrase for phrase in phrases if _has_phrase(text, phrase)]



def _active_payment_controls(html: str) -> list[str]:
    """Return explicit payment action labels found on actionable controls.

    Marketing text and generic service descriptions such as "accept payments"
    are deliberately excluded.
    """
    soup = BeautifulSoup(html or "", "html.parser")
    found = []
    for tag in soup.find_all(["button", "input", "a"], limit=250):
        label = " ".join([
            str(tag.get("value") or ""),
            str(tag.get("aria-label") or ""),
            tag.get_text(" ", strip=True),
        ]).strip().lower()
        for cue in ACTIVE_PAYMENT_ACTIONS:
            if _has_phrase(label, cue):
                found.append(cue)
    return list(dict.fromkeys(found))


def _checkout_path_detected(url: str) -> bool:
    raw_parts = [part.lower() for part in urlsplit(url or "").path.split("/") if part]
    path_tokens = []
    for part in raw_parts:
        # Also support route/file conventions such as demo_unverifiable_checkout.html.
        path_tokens.extend(
            token for token in re.split(r"[._-]+", part)
            if token
        )
    return any(token in CHECKOUT_PATH_SEGMENTS for token in path_tokens)


def _active_transaction_context(text: str) -> list[str]:
    return _matches((text or "").lower(), ACTIVE_TRANSACTION_CONTEXT)


def _extract_page_signals(response, html: str) -> dict:
    soup = BeautifulSoup(html or "", "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    description = ""
    meta = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    if meta:
        description = str(meta.get("content") or "")

    headings = " ".join(
        tag.get_text(" ", strip=True)
        for tag in soup.find_all(["h1", "h2", "h3"], limit=20)
    )
    cta_parts = []
    for tag in soup.find_all(["button", "a", "input"], limit=100):
        value = tag.get("value") or tag.get("aria-label") or tag.get_text(" ", strip=True)
        if value:
            cta_parts.append(str(value))
    cta_text = " ".join(cta_parts)

    form_parts = []
    for form in soup.find_all("form", limit=30):
        form_parts.append(str(form.get("id") or ""))
        form_parts.append(str(form.get("name") or ""))
        form_parts.append(str(form.get("action") or ""))
        for field in form.find_all(["input", "textarea", "select", "button"], limit=60):
            form_parts.append(" ".join(str(field.get(key) or "") for key in (
                "name", "id", "type", "placeholder", "aria-label", "autocomplete", "value"
            )))
            label = field.find_parent("label")
            if label:
                form_parts.append(label.get_text(" ", strip=True))
    form_text = " ".join(form_parts)

    body_text = soup.get_text(" ", strip=True)
    page_url = getattr(response, "url", "") or ""
    path = urlsplit(page_url).path.replace("/", " ").replace("-", " ").replace("_", " ")
    return {
        "title": title[:300],
        "description": description[:600],
        "headings": headings[:2000],
        "cta_text": cta_text[:3000],
        "form_text": form_text[:4000],
        "body_text": body_text[:12000],
        "path_text": path[:500],
        "form_count": len(soup.find_all("form")),
        "button_count": len(soup.find_all(["button", "input"], attrs={"type": re.compile("^(submit|button)$", re.I)})),
        "anchor_count": len(soup.find_all("a", href=True)),
    }


def classify_website_purpose(response, html: str) -> dict:
    """Return a deterministic, explainable page-purpose classification.

    The confidence value is a heuristic strength indicator, not a probability
    that the website is genuine, safe, or accurately classified.
    """
    signals = _extract_page_signals(response, html)
    weighted_sources = [
        ("title", signals["title"], 5.0),
        ("headings", signals["headings"], 4.0),
        ("description", signals["description"], 3.0),
        ("actions", signals["cta_text"], 3.0),
        ("forms", signals["form_text"], 2.0),
        ("url_path", signals["path_text"], 1.25),
        ("page_text", signals["body_text"], 0.35),
    ]
    scores = {category: 0.0 for category in CATEGORY_RULES}
    evidence = {category: [] for category in CATEGORY_RULES}

    for source_name, source_text, weight in weighted_sources:
        for category, phrases in CATEGORY_RULES.items():
            found = _matches(source_text, phrases)
            if found:
                # Repeated occurrences in one source should not dominate the result.
                unique_found = list(dict.fromkeys(found))[:5]
                scores[category] += weight * min(len(unique_found), 3)
                for phrase in unique_found:
                    evidence[category].append(f"{source_name}: '{phrase}'")

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_category, top_score = ranked[0] if ranked else ("unknown", 0.0)
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0

    if top_score < 3.0:
        category = "unknown"
        confidence = 0.20 if top_score == 0 else 0.30
    else:
        category = top_category
        # The value represents evidence strength and separation from runner-up.
        margin = max(0.0, top_score - second_score)
        confidence = min(0.95, 0.48 + min(top_score, 18.0) / 45.0 + min(margin, 10.0) / 50.0)
        if margin < 1.0:
            confidence = min(confidence, 0.58)

    secondary = [
        name for name, score in ranked[1:]
        if score >= max(3.0, top_score * 0.45) and name != category
    ][:2]

    # User-visible functions are kept separate from the broad purpose label.
    full_text = " ".join([
        signals["title"], signals["headings"], signals["description"],
        signals["cta_text"], signals["form_text"], signals["body_text"], signals["path_text"],
    ]).lower()
    functions = []
    if any(_has_phrase(full_text, x) for x in ["login", "sign in", "log in", "password"]):
        functions.append("Authentication / account access")
    if any(_has_phrase(full_text, x) for x in ["search", "search products", "search the site"]):
        functions.append("Search")
    if any(_has_phrase(full_text, x) for x in ["add to cart", "shopping cart", "product catalogue", "product catalog", "buy now"]):
        functions.append("Product browsing / cart")
    if any(_has_phrase(full_text, x) for x in ["book now", "reservation", "ticket booking", "flight booking", "hotel booking"]):
        functions.append("Booking / reservation")
    # Do not label a marketing headline (e.g., "Payment Gateway" or
    # "Accept Payments") as an active checkout action.
    active_controls = _active_payment_controls(html)
    active_context = _active_transaction_context(full_text)
    if active_controls or (active_context and _checkout_path_detected(getattr(response, "url", ""))):
        functions.append("Checkout / payment action")
    if signals["form_count"]:
        functions.append(f"Forms ({signals['form_count']} detected)")
    if any(_has_phrase(full_text, x) for x in ["article", "latest news", "headlines", "encyclopedia", "documentation"]):
        functions.append("Information / content reading")
    if not functions:
        functions.append("General information / navigation")

    return {
        "category": category,
        "label": CATEGORY_LABELS.get(category, CATEGORY_LABELS["unknown"]),
        "confidence": round(float(confidence), 2),
        "confidence_label": "High" if confidence >= 0.75 else "Moderate" if confidence >= 0.5 else "Low",
        "secondary_categories": secondary,
        "secondary_labels": [CATEGORY_LABELS[x] for x in secondary],
        "evidence": list(dict.fromkeys(evidence.get(category, [])))[:8],
        "detected_functions": list(dict.fromkeys(functions))[:8],
        "page_signals": {
            "title": signals["title"],
            "description": signals["description"],
            "headings": signals["headings"][:800],
            "form_count": signals["form_count"],
            "button_count": signals["button_count"],
            "anchor_count": signals["anchor_count"],
        },
        "method": "Explainable static-HTML keyword and structure heuristics; not a trained purpose classifier.",
    }


def detect_transaction_intent(response, html: str, page_data: dict | None = None) -> dict:
    """Decide whether the inspected page is in an active transaction step.

    Purpose wording (e.g. "payment gateway", "accept payments") is not enough
    to trigger PFIV. Strong evidence requires a payment-specific form, or a
    direct payment action combined with transaction context, or a checkout
    route combined with transaction context. Generic payment wording remains
    POTENTIAL and does not make PFIV applicable.
    """
    signals = _extract_page_signals(response, html)
    page_data = page_data or {}
    full_text = " ".join([
        signals["title"], signals["headings"], signals["cta_text"],
        signals["form_text"], signals["path_text"], signals["description"],
        signals["body_text"],
    ]).lower()

    payment_forms = page_data.get("payment_forms", [])
    page_payment_flag = bool(page_data.get("payment_page_detected"))
    controls = _active_payment_controls(html)
    context = _active_transaction_context(full_text)
    checkout_route = _checkout_path_detected(getattr(response, "url", ""))
    strong_matches = list(dict.fromkeys(controls + context))

    if payment_forms:
        status = "DETECTED"
        reason = "A form with payment-specific input fields was found in the inspected HTML."
        confidence = "High"
    elif controls and context:
        status = "DETECTED"
        reason = "An explicit payment action control and transaction-specific context were both found on this page."
        confidence = "High"
    elif checkout_route and context:
        status = "DETECTED"
        reason = "The inspected URL is a checkout/payment route and the page contains transaction-specific context."
        confidence = "Moderate"
    else:
        generic_matches = _matches(full_text, GENERIC_PAYMENT_CUES)
        # Generic service/marketing wording may indicate a payment-related
        # purpose, but it does not mean the current visitor is paying.
        if generic_matches or page_payment_flag or controls or checkout_route:
            status = "POTENTIAL"
            reason = "Payment-related purpose or wording exists, but active payment submission or checkout evidence was not established on this page."
            confidence = "Low"
        else:
            status = "NOT_DETECTED"
            reason = "No clear payment or transaction step was identified on the inspected page."
            confidence = "High"

    return {
        "status": status,
        "is_transaction_page": status == "DETECTED",
        "confidence_label": confidence,
        "strong_cues": strong_matches,
        "has_payment_form": bool(payment_forms),
        "explicit_payment_controls": controls,
        "transaction_context": context,
        "checkout_route": checkout_route,
        "reason": reason,
        "method": "Heuristic page-context check; static HTML may not expose dynamic JavaScript-only payment flows. Marketing wording alone does not trigger PFIV.",
    }

