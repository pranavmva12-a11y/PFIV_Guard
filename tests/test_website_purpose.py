"""Regression tests for purpose detection and PFIV applicability gating."""
from pathlib import Path
from types import SimpleNamespace

from requests import Response

from analysis_pipeline import analyze_page_security_context
from bankshield_core import extract_page_data, load_processor_map
from website_purpose import classify_website_purpose, detect_transaction_intent

BASE = Path(__file__).resolve().parents[1]
load_processor_map(str(BASE / "data" / "processors.json"))


def fake_response(url="https://example.test/"):
    response = Response()
    response.status_code = 200
    response.url = url
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.history = []
    return response


def purpose_for(url, html):
    return classify_website_purpose(fake_response(url), html)


def context_for_fixture(name):
    html = (BASE / "data" / name).read_text(encoding="utf-8")
    response = fake_response(f"http://localhost:8000/data/{name}")
    purpose, intent, payment = analyze_page_security_context(response, html)
    return purpose, intent, payment


def test_informational_site_is_not_a_payment_transaction():
    html = """<html><head><title>Example Encyclopedia</title>
    <meta name='description' content='A free encyclopedia and knowledge base'></head>
    <body><h1>Example Encyclopedia</h1><h2>Reference information</h2>
    <p>Read articles and documentation.</p></body></html>"""
    purpose = purpose_for("https://knowledge.example/", html)
    page = extract_page_data(fake_response(), html)
    intent = detect_transaction_intent(fake_response(), html, page)
    assert purpose["category"] == "informational"
    assert not intent["is_transaction_page"]
    assert intent["status"] == "NOT_DETECTED"


def test_ecommerce_page_purpose_is_detected():
    html = """<html><head><title>Online Shopping Store</title></head><body>
    <h1>Shop products</h1><button>Add to Cart</button><button>Buy Now</button>
    <p>Order history and product catalogue.</p></body></html>"""
    purpose = purpose_for("https://shop.example/", html)
    assert purpose["category"] == "ecommerce"
    assert "Product browsing / cart" in purpose["detected_functions"]


def test_banking_page_purpose_is_detected():
    html = """<html><head><title>Online Banking Services</title></head><body>
    <h1>Internet Banking</h1><p>Manage your savings account and fund transfer.</p>
    </body></html>"""
    purpose = purpose_for("https://bank.example/", html)
    assert purpose["category"] == "banking"


def test_payment_gateway_marketing_homepage_does_not_trigger_pfiv():
    html = """<html><head><title>Example Payment Gateway</title>
    <meta name='description' content='Accept online payments and manage merchant payouts'></head>
    <body><h1>Payment processing for businesses</h1>
    <p>Our payment platform helps merchants accept payments.</p>
    <a href='/products'>Explore products</a></body></html>"""
    response = fake_response("https://payments.example/")
    purpose = classify_website_purpose(response, html)
    page = extract_page_data(response, html)
    intent = detect_transaction_intent(response, html, page)
    assert purpose["category"] == "payment_gateway"
    assert not intent["is_transaction_page"]
    assert intent["status"] in {"POTENTIAL", "NOT_DETECTED"}


def test_login_password_form_is_not_mistaken_for_payment_form():
    html = """<html><head><title>Customer Login</title></head><body>
    <h1>Sign in to your account</h1><form action='/login' method='post'>
    <input name='username' type='text'><input name='password' type='password'>
    <button type='submit'>Sign in</button></form></body></html>"""
    response = fake_response("https://account.example/login")
    page = extract_page_data(response, html)
    intent = detect_transaction_intent(response, html, page)
    assert page["payment_forms"] == []
    assert len(page["credential_forms"]) == 1
    assert not intent["is_transaction_page"]


def test_checkout_page_triggers_pfiv():
    html = """<html><head><title>Checkout</title></head><body><h1>Secure Checkout</h1>
    <p>Enter card details to complete payment.</p><form action='/pay' method='post'>
    <input name='card_number'><input name='cvv'><button>Pay Now</button></form></body></html>"""
    response = fake_response("https://shop.example/checkout")
    page = extract_page_data(response, html)
    intent = detect_transaction_intent(response, html, page)
    assert intent["is_transaction_page"]
    assert intent["status"] == "DETECTED"


def test_all_four_controlled_pfiv_fixtures_remain_applicable_and_expected():
    expected = {
        "demo_legitimate_checkout.html": "Verified",
        "demo_checkout.html": "Suspicious",
        "demo_processor_mismatch.html": "Suspicious",
        "demo_unverifiable_checkout.html": "Unverifiable",
    }
    for fixture, expected_status in expected.items():
        _purpose, intent, payment = context_for_fixture(fixture)
        assert intent["is_transaction_page"], fixture
        assert payment["status"] == expected_status, fixture


def test_unknown_page_is_explicitly_unknown():
    html = "<html><head><title>Welcome</title></head><body><p>Hello.</p></body></html>"
    purpose = purpose_for("https://unclassified.example/", html)
    assert purpose["category"] == "unknown"
    assert purpose["confidence_label"] == "Low"


def test_payment_gateway_marketing_page_is_not_an_active_transaction():
    html = """<html><head><title>Razorpay - Payment Gateway for Online Payments</title>
    <meta name='description' content='Accept payments online with payment links and payment processing'></head>
    <body><h1>Payment Gateway</h1><p>Accept payments, payment links, payouts and online payments.</p>
    <a href='/products'>Explore products</a><a href='/solutions'>Accept payments</a>
    <button>Get Started</button></body></html>"""
    response = fake_response("https://gateway.example/")
    purpose = classify_website_purpose(response, html)
    page = extract_page_data(response, html)
    intent = detect_transaction_intent(response, html, page)
    _purpose, _intent, payment = analyze_page_security_context(response, html)
    assert purpose["category"] == "payment_gateway"
    assert intent["status"] == "POTENTIAL"
    assert not intent["is_transaction_page"]
    assert payment["status"] == "Not Applicable"
    assert payment["applicability"] == "Not Applicable"
    assert "Checkout / payment action" not in purpose["detected_functions"]


def test_pfiv_scoring_is_not_invoked_for_payment_gateway_marketing_page(monkeypatch):
    import analysis_pipeline

    html = (BASE / "data" / "purpose_fixtures" / "payment_gateway_home.html").read_text(encoding="utf-8")
    response = fake_response("https://gateway.example/")

    def should_not_run(*args, **kwargs):
        raise AssertionError("Full PFIV analysis must not run for a marketing homepage.")

    monkeypatch.setattr(analysis_pipeline, "analyze_payment_flow", should_not_run)
    purpose, intent, payment = analysis_pipeline.analyze_page_security_context(response, html)

    assert purpose["category"] == "payment_gateway"
    assert intent["status"] == "POTENTIAL"
    assert payment["status"] == "Not Applicable"
    assert payment["applicability"] == "Not Applicable"
    assert "were not run" in payment["evidence"][0]
