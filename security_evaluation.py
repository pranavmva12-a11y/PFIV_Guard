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
RESULT_DIR = BASE / "results" / "security_evaluation"

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
        "url": "http://localhost:8000/data/demo_legitimate_checkout.html",
        "expected": "Verified"
    },
    {
        "name": "External attacker endpoint",
        "url": "http://localhost:8000/data/demo_checkout.html",
        "expected": "Suspicious"
    },
    {
        "name": "Processor mismatch",
        "url": "http://localhost:8000/data/demo_processor_mismatch.html",
        "expected": "Suspicious"
    },
    {
        "name": "Unverifiable payment path",
        "url": "http://localhost:8000/data/demo_unverifiable_checkout.html",
        "expected": "Unverifiable"
    }
]


def run_case(case):

    total_start = time.perf_counter()

    response, html = fetch_page(
        case["url"], allow_local_fixture=True
    )

    fetch_end = time.perf_counter()

    website_purpose, transaction_intent, payment = analyze_page_security_context(
        response,
        html
    )

    pfiv_end = time.perf_counter()

    live_ml = predict_live_url(
        case["url"],
        response,
        html
    )

    ml_end = time.perf_counter()

    page = payment["page"]

    url_score, url_reasons = (
        url_risk_score(
            response.url,
            page
        )
    )

    ml_score = (
        live_ml["phishing_probability"]
        * 100
    )

    fusion = fuse_evidence(
        url_score=url_score,
        visual_score=None,  # no screenshot was supplied in this fixture
        payment_score=payment["score"],
        threat_score=None,  # no live threat-intelligence feed is connected
        ml_score=ml_score,
        payment_status=payment["status"]
    )

    total_end = time.perf_counter()

    total_time = (
        total_end
        - total_start
    )

    return {
        "Test Case": case["name"],
        "Website Purpose": website_purpose["label"],
        "Transaction Intent": transaction_intent["status"],
        "Expected PFIV": case["expected"],
        "Observed PFIV": payment["status"],
        "PFIV Score": payment["score"],
        "Final Classification": fusion["label"],
        "Final Risk Score": fusion["score"],
        "ML Prediction": live_ml["label"],
        "ML Probability (%)": round(
            ml_score,
            2
        ),
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
        "Intermediate Domains": len(
            payment["intermediate_domains"]
        ),
        "Fetch Time (s)": round(
            fetch_end - total_start,
            4
        ),
        "PFIV Analysis Time (s)": round(
            pfiv_end - fetch_end,
            4
        ),
        "ML Inference Time (s)": round(
            ml_end - pfiv_end,
            4
        ),
        "Total Analysis Time (s)": round(
            total_time,
            4
        ),
        "Pass": (
            payment["status"]
            == case["expected"]
        )
    }


def warm_up_model():
    """Load and warm the live model before timing cases for fairer steady-state timings."""
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
        "BANKSHIELD AI - SECURITY EVALUATION"
    )
    warm_up_model()

    print(
        "=" * 65
    )

    for case in TEST_CASES:

        try:

            result = run_case(
                case
            )

            rows.append(
                result
            )

            print(
                f"\n{result['Test Case']}"
            )

            print(
                "-" * 65
            )

            print(
                "Expected PFIV       :",
                result["Expected PFIV"]
            )

            print(
                "Observed PFIV       :",
                result["Observed PFIV"]
            )

            print(
                "PFIV Score          :",
                result["PFIV Score"]
            )

            print(
                "Final Classification:",
                result[
                    "Final Classification"
                ]
            )

            print(
                "Final Risk Score    :",
                result["Final Risk Score"]
            )

            print(
                "Processor           :",
                result["Processor"]
            )

            print(
                "Consistency         :",
                result[
                    "Processor Consistency"
                ]
            )

            print(
                "External Endpoints :",
                result[
                    "External Endpoints"
                ]
            )

            print(
                "Intermediate Domains:",
                result[
                    "Intermediate Domains"
                ]
            )

            print(
                "Total Time (s)      :",
                result[
                    "Total Analysis Time (s)"
                ]
            )

            print(
                "PASS                :",
                result["Pass"]
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
        / "security_evaluation_results.csv"
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

            writer.writerows(
                rows
            )

    passed = sum(
        1
        for row in rows
        if row["Pass"]
    )

    total = len(rows)

    summary = {
        "total_cases": total,
        "passed_cases": passed,
        "pass_rate_percent": round(
            passed / total * 100,
            2
        )
        if total
        else 0
    }

    (
        RESULT_DIR
        / "security_evaluation_summary.json"
    ).write_text(
        json.dumps(
            summary,
            indent=4
        ),
        encoding="utf-8"
    )

    print(
        "\n" + "=" * 65
    )

    print(
        "SECURITY EVALUATION COMPLETED"
    )

    print(
        "=" * 65
    )

    print(
        f"Passed cases: {passed}/{total}"
    )

    print(
        f"Pass rate   : "
        f"{summary['pass_rate_percent']}%"
    )

    print(
        "\nSaved:"
    )

    print(
        csv_path
    )

    print(
        RESULT_DIR
        / "security_evaluation_summary.json"
    )


if __name__ == "__main__":
    main()
