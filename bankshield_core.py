"""URL fetching and Payment Flow Integrity Verification for BankShield AI.

This module is a defensive research prototype. It never submits payment forms.
Public URL fetching blocks localhost/private destinations by default. Local demo
fixtures can only be fetched explicitly with allow_local_fixture=True.
"""
from __future__ import annotations

import ipaddress
import json
import re
import socket
from collections import Counter
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from domain_utils import registered_domain

USER_AGENT = "BankShieldAI/1.1 (defensive research prototype)"
CONNECT_TIMEOUT = 5
READ_TIMEOUT = 10
MAX_REDIRECTS = 5
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
LOCAL_FIXTURE_PORT = 8000

PAYMENT_TERMS = [
    "payment", "checkout", "pay now", "card number", "credit card",
    "debit card", "cvv", "cvc", "expiry", "expiration", "upi",
    "net banking", "bank account", "razorpay", "stripe", "paypal",
    "payu", "cashfree", "phonepe", "ccavenue", "billdesk", "adyen"
]
# Payment-specific fields are intentionally separate from login credentials.
# A normal username/password login form must not trigger payment-flow analysis.
SENSITIVE_TERMS = [
    "card_number", "cardnumber", "credit_card", "debit_card", "card",
    "cvv", "cvc", "expiry", "expiration", "upi", "iban", "swift",
    "routing_number", "bank_account_number", "account_number",
]
CREDENTIAL_TERMS = ["password", "passcode", "username", "user_name", "login", "otp", "pin"]
PAYMENT_PAGE_TERMS = [
    "checkout", "check out", "pay now", "pay securely", "complete payment",
    "proceed to payment", "payment details", "payment method", "card number",
    "credit card", "debit card", "cvv", "cvc", "expiry date", "billing address",
    "billing details", "place order", "confirm order", "order summary", "order total",
    "amount due", "upi id", "enter upi", "scan and pay", "pay bill", "bill payment",
    "transfer funds", "send money", "confirm and pay", "complete your purchase",
]
PROCESSOR_MAP = {}


class UnsafeTargetError(ValueError):
    """Raised when a target is invalid or resolves to a local/private network."""


def normalize_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        raise ValueError("Enter a website URL.")
    if len(raw) > 2048:
        raise ValueError("The URL is too long (maximum 2048 characters).")
    if any(c in raw for c in "\r\n\t"):
        raise ValueError("The URL contains invalid whitespace characters.")
    scheme_match = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*):", raw)
    if scheme_match:
        candidate_scheme = scheme_match.group(1).lower()
        if candidate_scheme not in {"http", "https"}:
            # Permit the common bare-host:port form such as example.com:8080.
            if re.match(r"^[A-Za-z0-9.-]+:\d+(?:/|\?|$)", raw):
                raw = "https://" + raw
            else:
                raise ValueError("Only HTTP and HTTPS website URLs are supported; non-web schemes are blocked.")
    else:
        raw = "https://" + raw
    parsed = urlsplit(raw)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS website URLs are supported.")
    if not parsed.hostname:
        raise ValueError("The URL does not contain a valid hostname.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URLs containing embedded username/password are not accepted.")
    try:
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("The URL contains an invalid port number.") from exc
    return raw


def hostname(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower()
    except Exception:
        return ""


def same_registered_domain(a: str, b: str) -> bool:
    return bool(a and b and registered_domain(a) == registered_domain(b))


def is_local_fixture_url(url: str) -> bool:
    """Only allow the project's named demo HTML files on localhost:8000."""
    try:
        p = urlsplit(normalize_url(url))
        host = (p.hostname or "").lower()
        port = p.port or (443 if p.scheme == "https" else 80)
        valid_host = host in {"localhost", "127.0.0.1", "::1"}
        valid_path = bool(re.fullmatch(r"/data/demo_[a-z0-9_-]+\.html", p.path, re.I))
        return p.scheme.lower() == "http" and port == LOCAL_FIXTURE_PORT and valid_host and valid_path
    except Exception:
        return False


def _check_target_safety(url: str, allow_local_fixture: bool) -> None:
    p = urlsplit(normalize_url(url))
    host = (p.hostname or "").strip("[]").lower()

    if allow_local_fixture and is_local_fixture_url(url):
        return

    if host in {"localhost", "localhost.localdomain"} or host.endswith((".localhost", ".local", ".internal")):
        raise UnsafeTargetError("Local/internal hostnames are blocked. Enable local demo mode only for the supplied localhost demo fixtures.")

    try:
        ip = ipaddress.ip_address(host)
        if not ip.is_global:
            raise UnsafeTargetError("Private, loopback, link-local and reserved IP addresses are blocked.")
        return
    except ValueError:
        pass

    # Resolve the host before each request/redirect and reject private results.
    try:
        infos = socket.getaddrinfo(host, p.port or (443 if p.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror:
        # Let the HTTP layer produce a readable DNS/connectivity error.
        return
    addresses = {item[4][0].split("%")[0] for item in infos}
    for address in addresses:
        try:
            resolved = ipaddress.ip_address(address)
        except ValueError:
            continue
        if not resolved.is_global:
            raise UnsafeTargetError(
                "The hostname resolves to a private or reserved network address, so fetching was blocked."
            )


def fetch_page(url: str, allow_local_fixture: bool = False):
    """Fetch an HTML page with bounded redirects/size and target validation."""
    current_url = normalize_url(url)
    local_mode = bool(allow_local_fixture and is_local_fixture_url(current_url))
    session = requests.Session()
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5"}
    history = []

    try:
        for redirect_number in range(MAX_REDIRECTS + 1):
            _check_target_safety(current_url, allow_local_fixture=local_mode)
            response = session.get(
                current_url,
                headers=headers,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                allow_redirects=False,
                stream=True,
            )

            if response.status_code in {301, 302, 303, 307, 308} and response.headers.get("Location"):
                location = urljoin(current_url, response.headers["Location"])
                response.close()
                history.append(response)
                current_url = normalize_url(location)
                if redirect_number >= MAX_REDIRECTS:
                    raise requests.TooManyRedirects(f"The URL exceeded {MAX_REDIRECTS} redirects.")
                # A local fixture is allowed to stay local only; redirects from it
                # to arbitrary hosts are checked as normal public targets.
                if local_mode and not is_local_fixture_url(current_url):
                    local_mode = False
                continue

            chunks = bytearray()
            truncated = False
            for chunk in response.iter_content(chunk_size=65536):
                if not chunk:
                    continue
                remaining = MAX_RESPONSE_BYTES - len(chunks)
                if len(chunk) > remaining:
                    chunks.extend(chunk[:remaining])
                    truncated = True
                    break
                chunks.extend(chunk)
                if len(chunks) >= MAX_RESPONSE_BYTES:
                    truncated = True
                    break
            response._content = bytes(chunks)
            response._content_consumed = True
            response.history = history
            if truncated:
                response.headers["X-BankShield-Content-Truncated"] = "true"
            return response, response.text

        raise requests.TooManyRedirects(f"The URL exceeded {MAX_REDIRECTS} redirects.")
    finally:
        session.close()


def redirect_chain(response):
    chain = []
    for item in getattr(response, "history", []) or []:
        chain.append({"status": item.status_code, "url": item.url, "domain": hostname(item.url)})
    chain.append({"status": response.status_code, "url": response.url, "domain": hostname(response.url)})
    return chain


def _blob(tag) -> str:
    return " ".join(str(tag.get(k) or "") for k in ["name", "id", "placeholder", "type", "autocomplete", "aria-label"]).lower()


def load_processor_map(path: str):
    global PROCESSOR_MAP
    with open(path, "r", encoding="utf-8") as f:
        PROCESSOR_MAP = json.load(f)
    return PROCESSOR_MAP


def identify_processor(domains):
    hits = Counter()
    for domain in domains:
        if not domain:
            continue
        registered = registered_domain(domain)
        for name, refs in PROCESSOR_MAP.items():
            reference_domains = {registered_domain(ref) for ref in refs}
            if registered in reference_domains:
                hits[name] += 1
    top = hits.most_common(1)
    return (top[0][0] if top else None, dict(hits))


def is_known_processor_domain(domain: str) -> bool:
    if not domain:
        return False
    rd = registered_domain(domain)
    known = {registered_domain(ref) for refs in PROCESSOR_MAP.values() for ref in refs}
    return rd in known


def extract_page_data(response, html: str) -> dict:
    soup = BeautifulSoup(html or "", "html.parser")
    base_url = response.url
    base_host = hostname(base_url)
    base_registered = registered_domain(base_host)
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    text = soup.get_text(" ", strip=True)
    visible_combined = (title + " " + text).lower()
    combined = (visible_combined + " " + (html or "")).lower()

    forms = []
    for form in soup.find_all("form"):
        action = urljoin(base_url, form.get("action") or "")
        fields = []
        payment_sensitive = False
        credential_sensitive = False
        for element in form.find_all(["input", "textarea", "select"]):
            token = _blob(element)
            fields.append(token)
            if any(term in token for term in SENSITIVE_TERMS):
                payment_sensitive = True
            if any(term in token for term in CREDENTIAL_TERMS):
                credential_sensitive = True
        forms.append({
            "method": (form.get("method") or "GET").upper(),
            "action": action,
            "domain": hostname(action),
            "sensitive": payment_sensitive or credential_sensitive,
            "payment_sensitive": payment_sensitive,
            "credential_sensitive": credential_sensitive,
            "inputs": fields,
        })

    iframe_domains = [hostname(urljoin(base_url, x.get("src", ""))) for x in soup.find_all("iframe", src=True)]
    script_domains = [hostname(urljoin(base_url, x.get("src", ""))) for x in soup.find_all("script", src=True)]
    payment_forms = [form for form in forms if form["payment_sensitive"]]
    credential_forms = [form for form in forms if form["credential_sensitive"]]
    # A generic login/password form is sensitive, but is not by itself a payment flow.
    # Claims come from visible page text/title, not from the form action itself.
    claimed_processors = [name for name in PROCESSOR_MAP if name.lower() in visible_combined]
    payment_detected = bool(payment_forms or any(term in combined for term in PAYMENT_PAGE_TERMS))

    return {
        "final_url": base_url,
        "base_domain": base_host,
        "registered_domain": base_registered,
        "title": title,
        "payment_page_detected": payment_detected,
        "payment_keyword_hits": sorted({term for term in PAYMENT_TERMS if term in combined}),
        "forms": forms,
        "payment_forms": payment_forms,
        "credential_forms": credential_forms,
        "iframe_domains": sorted({d for d in iframe_domains if d}),
        "script_domains": sorted({d for d in script_domains if d}),
        "claimed_processors": claimed_processors,
    }


def analyze_payment_flow(response, html: str) -> dict:
    page = extract_page_data(response, html)
    redirects = redirect_chain(response)
    redirect_domains = [item["domain"] for item in redirects if item["domain"]]
    endpoint_domains = [item["domain"] for item in page["payment_forms"] if item["domain"]]
    observed_domains = redirect_domains + endpoint_domains + page["iframe_domains"] + page["script_domains"]
    observed_processor, processor_hits = identify_processor(observed_domains)

    if not page["payment_page_detected"]:
        return {
            "status": "Not Applicable", "score": 0,
            "evidence": ["No clear payment/checkout page was detected."],
            "page": page, "processor": None, "processor_hits": {},
            "processor_consistency": "Not applicable", "external_endpoints": [],
            "intermediate_domains": [], "redirect_chain": redirects,
        }

    claimed = page["claimed_processors"]
    if not observed_processor:
        consistency = "Unknown"
    elif claimed:
        consistency = "Consistent" if observed_processor in claimed else "Mismatch"
    else:
        consistency = "Observed, claim not found"

    external_endpoints = [
        item["domain"] for item in page["payment_forms"]
        if item["domain"] and not same_registered_domain(item["domain"], page["base_domain"])
    ]
    suspicious_external = [domain for domain in external_endpoints if not is_known_processor_domain(domain)]
    known_processor_domains = {registered_domain(ref) for refs in PROCESSOR_MAP.values() for ref in refs}
    intermediate = sorted({
        domain for domain in observed_domains
        if domain and registered_domain(domain) != page["registered_domain"]
        and registered_domain(domain) not in known_processor_domains
    })

    observable_structure = bool(page["payment_forms"] or observed_processor or page["iframe_domains"] or page["script_domains"])
    if page["payment_page_detected"] and not observable_structure:
        return {
            "status": "Unverifiable", "score": 35,
            "evidence": ["A payment/checkout context was detected, but the observable sensitive payment path could not be established."],
            "page": page, "processor": None, "processor_hits": processor_hits,
            "processor_consistency": "Unknown", "external_endpoints": [],
            "intermediate_domains": [], "redirect_chain": redirects,
        }

    score = 0
    evidence = ["Payment/checkout indicators were detected."]
    if suspicious_external:
        score += 30
        evidence.append("A sensitive payment form submits to an unexpected external domain: " + ", ".join(sorted(set(suspicious_external))) + ".")
    elif external_endpoints:
        evidence.append("Sensitive payment submission goes to a known payment-processor domain: " + ", ".join(sorted(set(external_endpoints))) + ".")

    if consistency == "Mismatch":
        # Processor contradiction is a high-severity PFIV signal.
        score += 55
        evidence.append("The observed payment processor is inconsistent with the processor indicated by the page.")
    elif consistency == "Unknown":
        score += 15
        evidence.append("A payment page was detected, but no known payment processor could be identified.")
    elif consistency == "Consistent":
        evidence.append(f"Observed payment processor ({observed_processor}) is consistent with the processor evidence found on the page.")

    if intermediate:
        score += 20
        evidence.append("Unexpected/intermediary domains are present: " + ", ".join(intermediate[:8]) + ".")

    evidence.append(f"{len(page['payment_forms'])} potentially sensitive payment form(s) detected.")
    # A processor visible in a script/iframe is not enough to claim that the
    # sensitive submission path is verified. Require a payment-specific form
    # endpoint on a known processor domain, an explicit page claim matching
    # that processor, and no unexpected intermediary domains.
    verified_processor_endpoint = any(
        is_known_processor_domain(domain) for domain in endpoint_domains
    )
    verified_path = (
        consistency == "Consistent"
        and verified_processor_endpoint
        and not intermediate
        and not suspicious_external
    )

    if score >= 50:
        status = "Suspicious"
    elif score > 0:
        status = "Needs Review"
    elif verified_path:
        status = "Verified"
    elif observed_processor:
        # A processor was observed, but the complete sensitive submission path
        # was not sufficiently established to call it verified.
        status = "Needs Review"
    else:
        status = "Unverifiable"

    if getattr(response, "headers", {}).get("X-BankShield-Content-Truncated") == "true":
        evidence.append(f"The downloaded page was limited to {MAX_RESPONSE_BYTES // (1024 * 1024)} MB; later HTML content may not have been inspected.")

    return {
        "status": status,
        "score": min(score, 100),
        "evidence": evidence,
        "page": page,
        "processor": observed_processor,
        "processor_hits": processor_hits,
        "processor_consistency": consistency,
        "external_endpoints": sorted(set(external_endpoints)),
        "intermediate_domains": intermediate,
        "redirect_chain": redirects,
    }
