import io
import unittest
from shutil import which
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from bankshield_core import (
    normalize_url,
    is_local_fixture_url,
    _check_target_safety,
    UnsafeTargetError,
    load_processor_map,
    analyze_payment_flow,
)
from domain_utils import registered_domain
from fusion import fuse_evidence
from qr_branch import decode_qr_image
from visual_branch import analyze_screenshot, extract_urls

BASE = Path(__file__).resolve().parents[1]


class BankShieldInputTests(unittest.TestCase):
    def test_normalize_bare_domain(self):
        self.assertEqual(normalize_url("example.com"), "https://example.com")

    def test_reject_non_http_schemes(self):
        with self.assertRaises(ValueError):
            normalize_url("javascript:alert(1)")
        with self.assertRaises(ValueError):
            normalize_url("file:///C:/Windows/win.ini")

    def test_reject_embedded_credentials(self):
        with self.assertRaises(ValueError):
            normalize_url("https://user:pass@example.com")

    def test_local_fixture_allowlist_is_narrow(self):
        allowed = "http://localhost:8000/data/demo_processor_mismatch.html"
        not_allowed = "http://localhost:8000/admin"
        self.assertTrue(is_local_fixture_url(allowed))
        self.assertFalse(is_local_fixture_url(not_allowed))
        with self.assertRaises(UnsafeTargetError):
            _check_target_safety(allowed, allow_local_fixture=False)
        _check_target_safety(allowed, allow_local_fixture=True)
        with self.assertRaises(UnsafeTargetError):
            _check_target_safety(not_allowed, allow_local_fixture=True)

    def test_domain_parsing(self):
        self.assertEqual(registered_domain("checkout.stripe.com"), "stripe.com")
        self.assertEqual(registered_domain("shop.example.co.uk"), "example.co.uk")

    def test_screenshot_upload_without_ocr(self):
        image = Image.new("RGB", (900, 600), "white")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        result = analyze_screenshot(buffer.getvalue(), enable_ocr=False)
        self.assertTrue(result["available"])
        self.assertEqual(result["risk_score"], 0.0)
        self.assertIn("cannot inspect the actual network/payment submission path", result["limitations"][0])

    def test_extract_url_from_ocr_text(self):
        found = extract_urls("Open https://example.com/checkout or www.testsite.org/login now")
        self.assertIn("https://example.com/checkout", found)
        self.assertIn("https://www.testsite.org/login", found)

    def test_screenshot_ocr_extracts_text_and_pressure_signals(self):
        if which("tesseract") is None:
            self.skipTest("Tesseract executable is not installed; screenshot OCR runtime test skipped.")
        image = Image.new("RGB", (1100, 650), "white")
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.load_default(size=36)
        except TypeError:
            font = ImageFont.load_default()
        draw.text((50, 70), "URGENT: account suspended", fill="black", font=font)
        draw.text((50, 150), "Verify immediately and enter OTP", fill="black", font=font)
        draw.text((50, 230), "https://example.com/checkout", fill="black", font=font)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        result = analyze_screenshot(buffer.getvalue(), enable_ocr=True)
        self.assertTrue(result["ocr_available"])
        self.assertTrue(result["ocr_text"].strip())
        self.assertGreater(result["risk_score"], 0)
        self.assertTrue(any("example.com" in value for value in result["extracted_urls"]))

    def test_qr_decoder_reads_web_url(self):
        encoder = cv2.QRCodeEncoder_create()
        qr = encoder.encode("https://example.com/checkout")
        ok, encoded = cv2.imencode(".png", qr)
        self.assertTrue(ok)
        result = decode_qr_image(encoded.tobytes())
        self.assertTrue(result["available"])
        self.assertTrue(result["decoded"], result["evidence"])
        self.assertEqual(result["items"][0]["type"], "web_url")
        self.assertEqual(result["items"][0]["web_url"], "https://example.com/checkout")

    def test_qr_decoder_reads_upi_without_triggering_payment(self):
        encoder = cv2.QRCodeEncoder_create()
        qr = encoder.encode("upi://pay?pa=merchant%40upi&pn=Test%20Merchant&am=10.00&cu=INR")
        ok, encoded = cv2.imencode(".png", qr)
        self.assertTrue(ok)
        result = decode_qr_image(encoded.tobytes())
        self.assertTrue(result["decoded"], result["evidence"])
        self.assertEqual(result["items"][0]["type"], "upi_payment_uri")
        self.assertEqual(result["items"][0]["details"]["pa"], "merchant@upi")
        self.assertTrue(any("will not initiate a payment" in e for e in result["evidence"]))

    def test_processor_mismatch_pfiv_rule(self):
        load_processor_map(str(BASE / "data" / "processors.json"))
        from requests import Response
        html = (BASE / "data" / "demo_processor_mismatch.html").read_text(encoding="utf-8")
        response = Response()
        response.status_code = 200
        response.url = "http://localhost:8000/data/demo_processor_mismatch.html"
        response._content = html.encode("utf-8")
        response._content_consumed = True
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        response.history = []
        result = analyze_payment_flow(response, html)
        self.assertEqual(result["status"], "Suspicious")
        self.assertEqual(result["processor_consistency"], "Mismatch")


    def test_processor_resource_without_sensitive_endpoint_is_not_verified(self):
        load_processor_map(str(BASE / "data" / "processors.json"))
        from requests import Response
        html = """<html><head><title>Checkout</title></head><body>
        <h1>Secure Checkout</h1><p>Razorpay secure payment</p>
        <iframe src='https://checkout.razorpay.com/frame'></iframe>
        </body></html>"""
        response = Response()
        response.status_code = 200
        response.url = "https://merchant.example/checkout"
        response._content = html.encode("utf-8")
        response._content_consumed = True
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        response.history = []
        result = analyze_payment_flow(response, html)
        self.assertNotEqual(result["status"], "Verified")
        self.assertIn(result["status"], {"Needs Review", "Unverifiable"})

    def test_fusion_keeps_suspicious_pfiv_high_risk(self):
        result = fuse_evidence(
            url_score=0,
            visual_score=None,
            payment_score=55,
            threat_score=None,
            ml_score=24,
            payment_status="Suspicious",
        )
        self.assertEqual(result["label"], "High Risk")
        self.assertGreaterEqual(result["score"], 65)

    def test_strong_screenshot_indicator_is_at_least_suspicious(self):
        result = fuse_evidence(
            url_score=0,
            visual_score=65,
            payment_score=None,
            threat_score=None,
            ml_score=24,
            payment_status="Not Applicable",
        )
        self.assertEqual(result["label"], "Suspicious")
        self.assertGreaterEqual(result["score"], 40)


if __name__ == "__main__":
    unittest.main()
