"""Screenshot/OCR evidence extraction. This is heuristic support, not a trained CV model."""
from __future__ import annotations

import io
import re
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
URL_PATTERN = re.compile(r"(?i)\b(?:https?://|www\.)[a-z0-9][a-z0-9.-]*\.[a-z]{2,}(?::\d{1,5})?(?:/[^\s<>\"']*)?")

SUSPICIOUS_PHRASES = [
    "account suspended", "account blocked", "verify immediately", "verify now",
    "urgent action", "act immediately", "within 24 hours", "limited time",
    "account will be closed", "avoid suspension", "unusual activity detected",
    "claim your reward", "prize won", "update kyc immediately",
]
CREDENTIAL_TERMS = {"otp", "cvv", "cvc", "password", "pin", "card number", "bank account"}
PAYMENT_TERMS = {"payment", "checkout", "pay now", "upi", "debit card", "credit card", "card number", "cvv", "cvc"}


def extract_urls(text: str) -> list[str]:
    found = []
    for value in URL_PATTERN.findall(text or ""):
        cleaned = value.rstrip(".,);]}")
        if cleaned.lower().startswith("www."):
            cleaned = "https://" + cleaned
        if cleaned not in found:
            found.append(cleaned)
    return found[:20]


def analyze_screenshot(image_bytes: bytes, enable_ocr: bool = True) -> dict:
    result = {
        "available": True,
        "ocr_available": False,
        "risk_score": 0.0,
        "confidence": "Limited",
        "ocr_text": "",
        "detected_terms": [],
        "extracted_urls": [],
        "evidence": [],
        "limitations": ["Screenshot-only analysis cannot inspect the actual network/payment submission path."],
    }
    if not image_bytes:
        return {**result, "available": False, "evidence": ["No image data was supplied."]}
    if len(image_bytes) > MAX_IMAGE_BYTES:
        return {**result, "available": False, "evidence": [f"Image exceeds the {MAX_IMAGE_BYTES // (1024*1024)} MB upload limit."]}

    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            source.verify()
        with Image.open(io.BytesIO(image_bytes)) as source:
            width, height = source.size
            if width * height > MAX_IMAGE_PIXELS:
                return {**result, "available": False, "evidence": ["Image dimensions exceed the safe processing limit."]}
            image = ImageOps.exif_transpose(source).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        return {**result, "available": False, "evidence": [f"The uploaded file is not a supported image: {exc}"]}

    if width >= 900 and height >= 500:
        result["confidence"] = "Moderate"
    else:
        result["evidence"].append("The screenshot has limited resolution; OCR may miss small text.")

    if enable_ocr:
        try:
            import pytesseract
            text = pytesseract.image_to_string(image, config="--psm 6") or ""
            result["ocr_available"] = True
            result["ocr_text"] = text.strip()
        except Exception as exc:
            result["evidence"].append(
                "OCR could not run. Install the Tesseract OCR engine and verify its PATH. "
                f"Technical detail: {type(exc).__name__}"
            )

    lowered = result["ocr_text"].lower()
    if lowered:
        result["confidence"] = "Moderate" if len(lowered.strip()) >= 30 else "Limited"
        terms = sorted(term for term in (CREDENTIAL_TERMS | PAYMENT_TERMS) if term in lowered)
        result["detected_terms"] = terms
        result["extracted_urls"] = extract_urls(result["ocr_text"])
        if terms:
            result["evidence"].append("OCR found payment or credential-related text: " + ", ".join(terms) + ". These words provide context and do not by themselves prove fraud.")
        suspicious_hits = [phrase for phrase in SUSPICIOUS_PHRASES if phrase in lowered]
        if suspicious_hits:
            result["risk_score"] += min(20 * len(suspicious_hits), 40)
            result["evidence"].append("OCR found urgency/pressure language: " + ", ".join(suspicious_hits) + ".")
        if ({"otp", "cvv", "cvc"} & set(terms)) and ("urgent" in lowered or "immediately" in lowered or "suspended" in lowered):
            result["risk_score"] += 25
            result["evidence"].append("A sensitive credential term appears alongside urgency/pressure language.")
        if result["extracted_urls"]:
            result["evidence"].append(f"Extracted {len(result['extracted_urls'])} URL(s) from visible screenshot text; they can be sent to the URL analysis pipeline for a separate check.")
    else:
        result["evidence"].append("No readable text was extracted. This is not evidence that the page is safe.")

    result["risk_score"] = min(100.0, float(result["risk_score"]))
    return result
