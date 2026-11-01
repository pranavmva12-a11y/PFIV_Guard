"""QR decoding for BankShield AI using OpenCV's QRCodeDetector.

Decoded payment URIs are only inspected/displayed; no payment or network request is triggered.
"""
from __future__ import annotations

import io
import re
from urllib.parse import parse_qs, urlsplit

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_QR_IMAGE_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 40_000_000


def _looks_like_web_url(payload: str) -> bool:
    value = (payload or "").strip()
    if re.match(r"(?i)^https?://", value):
        return bool(urlsplit(value).hostname)
    if value.lower().startswith("www."):
        return True
    if " " not in value and re.fullmatch(r"(?i)[a-z0-9.-]+\.[a-z]{2,}(?::\d{1,5})?(?:/[^\s]*)?", value):
        return True
    return False


def _classify_payload(payload: str) -> dict:
    value = (payload or "").strip()
    if not value:
        return {"type": "empty", "is_web_url": False, "web_url": None, "details": {}}
    if _looks_like_web_url(value):
        web_url = value if re.match(r"(?i)^https?://", value) else "https://" + value
        return {"type": "web_url", "is_web_url": True, "web_url": web_url, "details": {}}
    if value.lower().startswith("upi://"):
        parsed = urlsplit(value)
        params = parse_qs(parsed.query)
        keys = ["pa", "pn", "mc", "tr", "am", "cu", "mode"]
        details = {key: (params.get(key, [""])[0]) for key in keys if params.get(key)}
        return {"type": "upi_payment_uri", "is_web_url": False, "web_url": None, "details": details}
    if value.lower().startswith(("intent:", "bankid:", "paytmmp:", "phonepe:")):
        return {"type": "app_or_payment_deep_link", "is_web_url": False, "web_url": None, "details": {}}
    return {"type": "plain_text_or_other", "is_web_url": False, "web_url": None, "details": {}}


def decode_qr_image(image_bytes: bytes) -> dict:
    result = {"available": True, "decoded": False, "payloads": [], "items": [], "evidence": []}
    if not image_bytes:
        return {**result, "available": False, "evidence": ["No image data was supplied."]}
    if len(image_bytes) > MAX_QR_IMAGE_BYTES:
        return {**result, "available": False, "evidence": [f"Image exceeds the {MAX_QR_IMAGE_BYTES // (1024*1024)} MB upload limit."]}
    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            source.verify()
        with Image.open(io.BytesIO(image_bytes)) as source:
            if source.width * source.height > MAX_PIXELS:
                return {**result, "available": False, "evidence": ["Image dimensions exceed the safe processing limit."]}
            rgb = ImageOps.exif_transpose(source).convert("RGB")
            frame = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
            # Phone screenshots are often large; generated/test QR fixtures may be
            # only a few dozen pixels. Upscale small codes and add a white quiet zone.
            shortest = min(frame.shape[0], frame.shape[1])
            if shortest < 350:
                scale = max(3.0, 350.0 / max(shortest, 1))
                frame = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
            frame = cv2.copyMakeBorder(frame, 24, 24, 24, 24, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        return {**result, "available": False, "evidence": [f"The uploaded file is not a supported image: {exc}"]}

    detector = cv2.QRCodeDetector()
    payloads = []
    try:
        ok, decoded_info, _points, _straight = detector.detectAndDecodeMulti(frame)
        if ok and decoded_info:
            payloads.extend(text.strip() for text in decoded_info if text and text.strip())
    except (cv2.error, AttributeError, TypeError):
        pass
    if not payloads:
        try:
            single, _points, _straight = detector.detectAndDecode(frame)
            if single and single.strip():
                payloads.append(single.strip())
        except cv2.error:
            pass

    # Preserve order and remove duplicate payloads.
    payloads = list(dict.fromkeys(payloads))
    items = []
    for payload in payloads:
        item = {"payload": payload}
        item.update(_classify_payload(payload))
        items.append(item)

    result["decoded"] = bool(items)
    result["payloads"] = payloads
    result["items"] = items
    if not items:
        result["evidence"].append("No readable QR payload was detected. Try a sharper, well-lit image with the entire QR code visible.")
    else:
        result["evidence"].append(f"Decoded {len(items)} QR payload(s). Decoding does not establish that the destination is legitimate.")
        if any(item["type"] == "upi_payment_uri" for item in items):
            result["evidence"].append("A UPI/payment URI was found. BankShield will not initiate a payment; verify the payee independently in your payment app.")
    return result
