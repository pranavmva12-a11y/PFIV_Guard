# Synthetic input fixtures

These are generated demo images, not real banking or payment QR codes.

- `demo_qr_public_url.png`: QR contains `https://www.example.com/`.
- `demo_qr_processor_mismatch.png`: QR contains the local processor-mismatch HTML fixture. Start `python -m http.server 8000 --bind 127.0.0.1` and enable local demo mode in the sidebar before analysis.
- `demo_qr_upi.png`: QR contains a clearly synthetic UPI URI for decoding demonstration only. Do not use it to initiate a payment.
- `demo_checkout_screenshot.png`: synthetic checkout screenshot with OCR-readable demo text; contains no real credentials or payment brand.
