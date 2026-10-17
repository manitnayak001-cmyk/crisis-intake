
import json
from pathlib import Path

from database import init_db, list_cases
from models import CaseFile
from agents.caller_agent import load_scenario
from evaluation import evaluate_case


def main():
    init_db()

    saved_cases = list_cases(limit=1)

    if not saved_cases:
        print("No saved cases found. Run main_simulation.py first.")
        return

    saved = saved_cases[0]
    actual_case = CaseFile.model_validate(saved["case"])

    scenario_path = (
        Path(__file__).parent
        / "scenarios"
        / "road_accident.json"
    )
    scenario = load_scenario(str(scenario_path))

    expected = {
        "incident_type": scenario.get("incident_type"),
        "location": scenario.get("location"),
        "immediate_danger": scenario.get("immediate_danger"),
        "people_affected": scenario.get("people_affected"),
        "urgency": scenario.get("urgency"),
    }

    report = evaluate_case(actual_case, expected)

    print("\n=== CASE EVALUATION REPORT ===")
    print(f"Case ID: {saved['id']}")

    for field, result in report["field_results"].items():
        status = "PASS" if result["passed"] else "FAIL"

        print(f"\n[{status}] {field}")
        print(f"  Expected: {result['expected']}")
        print(f"  Actual:   {result['actual']}")

    print("\n=== SUMMARY ===")
    print(f"Field checks passed: {report['passed']}/{report['total']}")
    print(f"Field accuracy: {report['accuracy_percent']}%")
    print(
        "Required fields complete:",
        report["completeness"]["complete"],
    )

    missing = report["completeness"]["missing_fields"]
    print("Missing required fields:", missing)


if __name__ == "__main__":
    main()
