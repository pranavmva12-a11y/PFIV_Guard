
from pathlib import Path
import csv
import json
import time

from bankshield_core import (
    load_processor_map,
    fetch_page,
)
from analysis_pipeline import analyze_page_security_context
from fusion import (
    url_risk_score,
    fuse_evidence
)
from live_ml import predict_live_url


BASE = Path(__file__).resolve().parent
PROCESSOR_FILE = BASE / "data" / "processors.json"

RESULT_DIR = BASE / "results" / "ablation"
RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

load_processor_map(
    str(PROCESSOR_FILE)
)

TEST_CASES = [
    {
        "name": "Legitimate payment path",
        "url": "http://localhost:8000/data/demo_legitimate_checkout.html"
    },
    {
        "name": "External attacker endpoint",
        "url": "http://localhost:8000/data/demo_checkout.html"
    },
    {
        "name": "Processor mismatch",
        "url": "http://localhost:8000/data/demo_processor_mismatch.html"
    },
    {
        "name": "Unverifiable payment path",
        "url": "http://localhost:8000/data/demo_unverifiable_checkout.html"
    }
]


def baseline_without_pfiv(
    url_score,
    ml_score,
    visual_score=0.0,
    threat_score=0.0
):
    """
    Baseline = the same *available* non-PFIV evidence, re-normalized
    after removing PFIV. Screenshot evidence is absent in these HTML fixtures
    and live threat intelligence is not connected, so neither branch is
    treated as a zero-risk observation.

    Available baseline weights:
        URL = 0.25
        ML  = 0.25

    Their normalized total is 0.50.
    """

    remaining_weight = 0.25 + 0.25

    score = (
        (0.25 / remaining_weight) * url_score
        + (0.25 / remaining_weight) * ml_score
    )

    score = round(
        max(0.0, min(100.0, score)),
        2
    )

    if score >= 65:
        label = "High Risk"
    elif score >= 35:
        label = "Suspicious"
    else:
        label = "Legitimate"

    return score, label


def run_case(case):

    total_start = time.perf_counter()

    response, html = fetch_page(
        case["url"], allow_local_fixture=True
    )

    website_purpose, transaction_intent, payment = analyze_page_security_context(
        response,
        html
    )

    page = payment["page"]

    url_score, _ = url_risk_score(
        response.url,
        page
    )

    live_ml = predict_live_url(
        case["url"],
        response,
        html
    )

    ml_score = (
        live_ml["phishing_probability"]
        * 100
    )

    # Full system: PFIV included
    full_system = fuse_evidence(
        url_score=url_score,
        visual_score=None,  # no screenshot was supplied in this fixture
        payment_score=payment["score"],
        threat_score=None,  # no live threat-intelligence feed is connected
        ml_score=ml_score,
        payment_status=payment["status"]
    )

    # Ablated system: PFIV removed
    baseline_score, baseline_label = (
        baseline_without_pfiv(
            url_score=url_score,
            ml_score=ml_score
        )
    )

    total_time = (
        time.perf_counter()
        - total_start
    )

    decision_changed = (
        baseline_label
        != full_system["label"]
    )

    risk_increase = round(
        full_system["score"]
        - baseline_score,
        2
    )

    return {
        "Test Case": case["name"],
        "Website Purpose": website_purpose["label"],
        "Transaction Intent": transaction_intent["status"],
        "PFIV Status": payment["status"],
        "PFIV Score": payment["score"],
        "Processor": (
            payment["processor"]
            or "Not identified"
        ),
        "Processor Consistency": (
            payment["processor_consistency"]
        ),
        "External Endpoints": len(
            payment["external_endpoints"]
        ),
        "ML Prediction": live_ml["label"],
        "ML Probability (%)": round(
            ml_score,
            2
        ),
        "Baseline Without PFIV Score": baseline_score,
        "Baseline Without PFIV": baseline_label,
        "Full System With PFIV Score": full_system["score"],
        "Full System With PFIV": full_system["label"],
        "Risk Increase Due To PFIV": risk_increase,
        "Decision Changed": decision_changed,
        "Total Analysis Time (s)": round(
            total_time,
            4
        )
    }


def warm_up_model():
    """Warm the model so the first case does not uniquely include model loading."""
    try:
        first = TEST_CASES[0]
        response, html = fetch_page(first["url"], allow_local_fixture=True)
        predict_live_url(first["url"], response, html)
        print("Warm-up: model loaded before per-case timing measurements.")
    except Exception as exc:
        print(f"Warm-up could not complete; first timing may include cold-start cost: {exc}")


def main():

    rows = []

    print(
        "BANKSHIELD AI - PFIV ABLATION STUDY"
    )
    warm_up_model()

    print(
        "=" * 70
    )

    for case in TEST_CASES:

        try:
            result = run_case(case)
            rows.append(result)

            print(
                f"\n{result['Test Case']}"
            )

            print(
                "-" * 70
            )

            print(
                "PFIV Status              :",
                result["PFIV Status"]
            )

            print(
                "PFIV Score               :",
                result["PFIV Score"]
            )

            print(
                "Processor                :",
                result["Processor"]
            )

            print(
                "Consistency              :",
                result["Processor Consistency"]
            )

            print(
                "Baseline Without PFIV   :",
                result["Baseline Without PFIV"],
                f"({result['Baseline Without PFIV Score']})"
            )

            print(
                "Full System With PFIV   :",
                result["Full System With PFIV"],
                f"({result['Full System With PFIV Score']})"
            )

            print(
                "Risk Increase            :",
                result["Risk Increase Due To PFIV"]
            )

            print(
                "Decision Changed         :",
                result["Decision Changed"]
            )

        except Exception as exc:

            print(
                f"\n{case['name']}"
            )

            print(
                "ERROR:",
                exc
            )

    csv_path = (
        RESULT_DIR
        / "pfiv_ablation_results.csv"
    )

    if rows:

        with open(
            csv_path,
            "w",
            newline="",
            encoding="utf-8"
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=rows[0].keys()
            )

            writer.writeheader()
            writer.writerows(rows)

    changed = sum(
        1
        for row in rows
        if row["Decision Changed"]
    )

    summary = {
        "cases": len(rows),
        "decision_changes_due_to_pfiv": changed,
        "decision_change_rate_percent": round(
            changed / len(rows) * 100,
            2
        ) if rows else 0,
        "note": (
            "Controlled four-case ablation study. "
            "This is a proof-of-concept contribution analysis, "
            "not a statistically generalizable accuracy estimate."
        )
    }

    (
        RESULT_DIR
        / "pfiv_ablation_summary.json"
    ).write_text(
        json.dumps(
            summary,
            indent=4
        ),
        encoding="utf-8"
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "PFIV ABLATION STUDY COMPLETED"
    )

    print(
        "=" * 70
    )

    print(
        f"Decision changes due to PFIV: "
        f"{changed}/{len(rows)}"
    )

    print(
        f"Decision change rate: "
        f"{summary['decision_change_rate_percent']}%"
    )

    print(
        "\nSaved:"
    )

    print(
        csv_path
    )

    print(
        RESULT_DIR
        / "pfiv_ablation_summary.json"
    )


if __name__ == "__main__":
    main()
