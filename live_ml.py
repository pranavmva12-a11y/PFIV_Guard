from pathlib import Path
from urllib.parse import urljoin, urlparse
import re
import socket
import ipaddress
from functools import lru_cache

import joblib
import pandas as pd
from bs4 import BeautifulSoup
from domain_utils import registered_domain

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "random_forest.pkl"


@lru_cache(maxsize=1)
def _load_model():
    """Load the trained model once per Python process, not once per URL."""
    return joblib.load(MODEL_PATH)

SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
    "is.gd", "buff.ly", "cutt.ly", "rebrand.ly"
}

FEATURES = [
    "having_ip_address", "url_length", "shortining_service",
    "having_at_symbol", "double_slash_redirecting", "prefix_suffix",
    "having_sub_domain", "sslfinal_state", "domain_registration_length",
    "favicon", "port", "https_token", "request_url", "url_of_anchor",
    "links_in_tags", "sfh", "submitting_to_email", "abnormal_url",
    "redirect", "on_mouseover", "rightclick", "popupwindow", "iframe",
    "age_of_domain", "dnsrecord", "web_traffic", "page_rank",
    "google_index", "links_pointing_to_page", "statistical_report"
]


def is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def tri_state(value: float, good_threshold: float, bad_threshold: float) -> int:
    if value < good_threshold:
        return 1
    if value <= bad_threshold:
        return 0
    return -1


def extract_live_features(url: str, response, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    parsed = urlparse(response.url)
    host = parsed.hostname or ""
    page_domain = registered_domain(host)
    low_html = html.lower()

    features = {}

    # Address-bar features
    features["having_ip_address"] = -1 if is_ip(host) else 1
    n = len(url)
    features["url_length"] = 1 if n < 54 else 0 if n <= 75 else -1
    features["shortining_service"] = -1 if page_domain in SHORTENER_DOMAINS else 1
    features["having_at_symbol"] = -1 if "@" in url else 1
    features["double_slash_redirecting"] = -1 if "//" in (parsed.path or "") else 1

    hostname_label = host.split(".")[0] if host else ""
    features["prefix_suffix"] = -1 if "-" in hostname_label else 1

    parts = host.split(".") if host and not is_ip(host) else []
    if parts and parts[0].lower() == "www":
        parts = parts[1:]
    sub_count = max(0, len(parts) - 2) if parts else 0
    features["having_sub_domain"] = 1 if sub_count <= 1 else 0 if sub_count == 2 else -1

    features["sslfinal_state"] = 1 if parsed.scheme.lower() == "https" else -1

    # WHOIS-based values are optional. Unknown -> 0 for this prototype.
    age_days = None
    expiry_days = None
    try:
        import whois
        from datetime import datetime, timezone

        record = whois.whois(host)
        created = record.creation_date
        expires = record.expiration_date

        if isinstance(created, list):
            created = created[0]
        if isinstance(expires, list):
            expires = expires[0]

        now = datetime.now(timezone.utc)
        if created:
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age_days = (now - created).days
        if expires:
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            expiry_days = (expires - now).days
    except Exception:
        pass

    features["age_of_domain"] = 0 if age_days is None else (1 if age_days > 365 else -1)
    features["domain_registration_length"] = 0 if expiry_days is None else (1 if expiry_days > 365 else -1)

    # Favicon
    favicon = None
    for link in soup.find_all("link"):
        rel = " ".join(link.get("rel") or []).lower()
        if "icon" in rel and link.get("href"):
            favicon = urljoin(response.url, link["href"])
            break
    if favicon:
        fh = urlparse(favicon).hostname or ""
        features["favicon"] = 1 if registered_domain(fh) == page_domain else -1
    else:
        features["favicon"] = 0

    features["port"] = 1 if parsed.port in (None, 80, 443) else -1
    features["https_token"] = -1 if "https" in host.lower() else 1

    # External resources
    resources = []
    for tag in soup.find_all(["img", "script", "iframe", "audio", "video", "source"]):
        src = tag.get("src")
        if src:
            resources.append(urljoin(response.url, src))
    for tag in soup.find_all("link", href=True):
        resources.append(urljoin(response.url, tag["href"]))

    ext_resources = 0
    for r in resources:
        rh = urlparse(r).hostname or ""
        if rh and registered_domain(rh) != page_domain:
            ext_resources += 1
    resource_pct = (ext_resources / len(resources) * 100) if resources else 0
    features["request_url"] = tri_state(resource_pct, 22, 61)

    # External anchor proportion
    anchors = soup.find_all("a", href=True)
    ext_anchors = 0
    for a in anchors:
        target = urljoin(response.url, a["href"])
        ah = urlparse(target).hostname or ""
        if ah and registered_domain(ah) != page_domain:
            ext_anchors += 1
    anchor_pct = (ext_anchors / len(anchors) * 100) if anchors else 0
    features["url_of_anchor"] = tri_state(anchor_pct, 31, 67)

    # External links in meta/script/link tags
    tagged_links = []
    for tag in soup.find_all(["meta", "script", "link"]):
        value = tag.get("src") or tag.get("href")
        if value:
            tagged_links.append(urljoin(response.url, value))
    ext_tagged = 0
    for target in tagged_links:
        th = urlparse(target).hostname or ""
        if th and registered_domain(th) != page_domain:
            ext_tagged += 1
    tag_pct = (ext_tagged / len(tagged_links) * 100) if tagged_links else 0
    features["links_in_tags"] = tri_state(tag_pct, 17, 81)

    # Form handler / sensitive form destination
    forms = soup.find_all("form")
    if not forms:
        features["sfh"] = 0
    else:
        external_form = False
        email_form = False
        for form in forms:
            action = (form.get("action") or "").strip()
            if action.lower().startswith("mailto:"):
                email_form = True
                continue
            target = urljoin(response.url, action)
            th = urlparse(target).hostname or ""
            if th and registered_domain(th) != page_domain:
                external_form = True
        features["sfh"] = -1 if (email_form or external_form) else 1

    features["submitting_to_email"] = -1 if re.search(r"mailto\s*:", html, re.I) else 1

    original_host = urlparse(url).hostname or ""
    response_host = urlparse(response.url).hostname or ""
    features["abnormal_url"] = 1 if registered_domain(original_host) == registered_domain(response_host) else -1

    redirects = len(getattr(response, "history", []))
    features["redirect"] = 1 if redirects == 0 else 0 if redirects <= 2 else -1
    features["on_mouseover"] = -1 if "onmouseover" in low_html else 1
    features["rightclick"] = -1 if ("contextmenu" in low_html or "event.button==2" in low_html or "event.button == 2" in low_html) else 1
    features["popupwindow"] = -1 if "window.open(" in low_html else 1
    features["iframe"] = -1 if soup.find("iframe") else 1

    # These require external / historical services and are intentionally unavailable here.
    features["web_traffic"] = 0
    features["page_rank"] = 0
    features["google_index"] = 0
    features["links_pointing_to_page"] = 0
    features["statistical_report"] = 0

    return {f: int(features.get(f, 0)) for f in FEATURES}


def predict_live_url(url: str, response, html: str) -> dict:
    model = _load_model()
    feature_dict = extract_live_features(url, response, html)
    X_live = pd.DataFrame([[feature_dict[f] for f in FEATURES]], columns=FEATURES)

    pred = int(model.predict(X_live)[0])
    probabilities = model.predict_proba(X_live)[0]
    classes = list(model.classes_)
    phishing_index = classes.index(1) if 1 in classes else len(classes) - 1
    probability = float(probabilities[phishing_index])

    return {
        "prediction": pred,
        "label": "Phishing" if pred == 1 else "Legitimate",
        "phishing_probability": probability,
        "features": feature_dict
    }
