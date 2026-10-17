
from models import CaseFile
from agents.tools import check_completeness


# Fields with expected values that we can compare directly.
EVALUATED_FIELDS = [
    "incident_type",
    "location",
    "immediate_danger",
    "people_affected",
    "urgency",
]


def evaluate_case(
    actual: CaseFile,
    expected: dict,
) -> dict:
    """Compare a CaseFile with the expected scenario facts."""

    field_results = {}

    for field in EVALUATED_FIELDS:
        expected_value = expected.get(field)

        # Don't score fields without a known expected value.
        if expected_value is None:
            continue

        actual_value = getattr(actual, field)
        passed = actual_value == expected_value

        field_results[field] = {
            "expected": expected_value,
            "actual": actual_value,
            "passed": passed,
        }

    total = len(field_results)
    passed = sum(
        result["passed"]
        for result in field_results.values()
    )

    accuracy = (passed / total * 100) if total else 0.0

    return {
        "field_results": field_results,
        "passed": passed,
        "total": total,
        "accuracy_percent": round(accuracy, 2),
        "completeness": check_completeness(actual),
    }
