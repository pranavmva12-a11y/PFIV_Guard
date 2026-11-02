"""Regression tests for the safe British Airways-style incident simulation."""
from incident_simulation_ba2018 import run_simulation


def _by_id(report):
    return {case["scenario_id"]: case for case in report["cases"]}


def test_simulation_never_uses_network_or_real_payment_data():
    report = run_simulation(write_json=False)
    assert report["network_requests"] == 0
    assert report["payment_form_submissions"] == 0
    assert report["real_credentials_or_card_data_used"] is False


def test_visible_attacker_payment_endpoint_is_flagged():
    report = _by_id(run_simulation(write_json=False))
    case = report["visible_attacker_form_endpoint"]
    assert case["observed_pfiv_status"] == "Suspicious"
    assert case["pfiv_score"] >= 50
    assert "baways.example" in case["external_payment_endpoints"]


def test_external_script_host_is_visible_as_review_signal():
    report = _by_id(run_simulation(write_json=False))
    case = report["external_skimmer_script"]
    assert case["observed_pfiv_status"] == "Needs Review"
    assert "baways.example" in case["script_domains"]


def test_inline_script_exfiltration_is_not_parsed_by_current_static_pfiv():
    report = _by_id(run_simulation(write_json=False))
    case = report["inline_javascript_skimmer"]
    assert case["observed_pfiv_status"] == "Needs Review"
    assert "baways.example" not in case["script_domains"]
    assert case["static_pfiv_mentions_baways"] is False


def test_legitimate_known_processor_control_is_verified():
    report = _by_id(run_simulation(write_json=False))
    case = report["legitimate_processor_control"]
    assert case["observed_pfiv_status"] == "Verified"
    assert case["processor"] == "Stripe"
