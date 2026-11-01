"""Offline, deterministic validation of website-purpose detection and PFIV gating.

Uses local synthetic HTML fixtures only. It does not fetch public websites and
is not a phishing-detection accuracy benchmark.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from requests import Response

from analysis_pipeline import analyze_page_security_context
from bankshield_core import load_processor_map

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
RESULTS = BASE / "results" / "wpfd_pfiv_validation"
RESULTS.mkdir(parents=True, exist_ok=True)
load_processor_map(str(DATA / "processors.json"))

CASES = [
    ("Informational page", "purpose_fixtures/informational.html", "informational", "NOT_DETECTED", "Not Applicable"),
    ("E-commerce catalogue", "purpose_fixtures/ecommerce.html", "ecommerce", "NOT_DETECTED", "Not Applicable"),
    ("Banking homepage", "purpose_fixtures/banking.html", "banking", "NOT_DETECTED", "Not Applicable"),
    ("Payment gateway marketing page", "purpose_fixtures/payment_gateway_home.html", "payment_gateway", "POTENTIAL", "Not Applicable"),
    ("Train booking page", "purpose_fixtures/booking.html", "booking", "NOT_DETECTED", "Not Applicable"),
    ("Login form", "purpose_fixtures/login.html", "unknown", "NOT_DETECTED", "Not Applicable"),
    ("Legitimate payment checkout", "demo_legitimate_checkout.html", "unknown", "DETECTED", "Verified"),
    ("External attacker endpoint", "demo_checkout.html", "unknown", "DETECTED", "Suspicious"),
    ("Processor mismatch", "demo_processor_mismatch.html", "unknown", "DETECTED", "Suspicious"),
    ("Unverifiable checkout", "demo_unverifiable_checkout.html", "unknown", "DETECTED", "Unverifiable"),
]


def _response(url: str) -> Response:
    response = Response()
    response.status_code = 200
    response.url = url
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.history = []
    return response


def main() -> int:
    rows = []
    for name, relative_path, expected_purpose, expected_intent, expected_pfiv in CASES:
        html = (DATA / relative_path).read_text(encoding="utf-8")
        url = f"http://localhost:8000/data/{relative_path.replace(chr(92), '/') }"
        response = _response(url)
        purpose, intent, pfiv = analyze_page_security_context(response, html)
        purpose_match = purpose["category"] == expected_purpose
        intent_match = intent["status"] == expected_intent
        pfiv_match = pfiv["status"] == expected_pfiv
        rows.append({
            "Scenario": name,
            "Expected Purpose": expected_purpose,
            "Observed Purpose": purpose["category"],
            "Purpose Match": purpose_match,
            "Expected Transaction Intent": expected_intent,
            "Observed Transaction Intent": intent["status"],
            "Intent Match": intent_match,
            "Expected PFIV": expected_pfiv,
            "Observed PFIV": pfiv["status"],
            "PFIV Match": pfiv_match,
            "Pass": purpose_match and intent_match and pfiv_match,
            "Purpose Evidence": " | ".join(purpose.get("evidence", [])),
        })

    csv_path = RESULTS / "wpfd_pfiv_fixture_results.csv"
    json_path = RESULTS / "wpfd_pfiv_fixture_summary.json"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "scope": "10 synthetic HTML fixtures; deterministic purpose and PFIV applicability validation only",
        "cases": len(rows),
        "passed": sum(row["Pass"] for row in rows),
        "failed": sum(not row["Pass"] for row in rows),
        "not_a_real_world_accuracy_measure": True,
        "csv": str(csv_path.relative_to(BASE)),
    }
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("PFIV GUARD - WEBSITE PURPOSE + PFIV FIXTURE VALIDATION")
    print("=" * 68)
    for row in rows:
        print(f"{row['Scenario']}: purpose={row['Observed Purpose']}, intent={row['Observed Transaction Intent']}, PFIV={row['Observed PFIV']} -> {'PASS' if row['Pass'] else 'FAIL'}")
    print(f"\nPassed: {summary['passed']}/{summary['cases']}")
    print(f"Saved: {csv_path}\nSaved: {json_path}")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
