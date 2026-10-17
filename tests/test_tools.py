import pytest

from agents.tools import update_case_field, is_case_complete, check_completeness, execute_tool
from models import CaseFile
from agents.tools import finalize_case


def test_update_case_field_accepts_string():
    case = CaseFile()

    result = update_case_field(case, "caller_name", "Manit")

    assert result["success"] is True
    assert case.caller_name == "Manit"


def test_update_case_field_accepts_boolean():
    case = CaseFile()

    result = update_case_field(case, "immediate_danger", True)

    assert result["success"] is True
    assert case.immediate_danger is True


def test_update_case_field_rejects_string_boolean():
    case = CaseFile()

    with pytest.raises(ValueError, match="must be a boolean"):
        update_case_field(case, "immediate_danger", "true")

    assert case.immediate_danger is None


def test_update_case_field_rejects_string_integer():
    case = CaseFile()

    with pytest.raises(ValueError, match="must be an integer"):
        update_case_field(case, "people_affected", "3")

    assert case.people_affected is None

def test_case_is_incomplete_initially():
    case = CaseFile()

    assert is_case_complete(case) is False


def test_case_is_complete_when_required_fields_exist():
    case = CaseFile()

    case.location = "123 Main Street"
    case.incident_type = "fire"
    case.description = "Kitchen fire"
    case.immediate_danger = True
    case.urgency = "critical"

    assert is_case_complete(case) is True


def test_finalize_case_rejects_incomplete_case():
    case = CaseFile()

    result = finalize_case(
        case,
        "Fire at 123 Main Street."
    )

    assert result["success"] is False
    assert result["error"] == "Cannot finalize incomplete case"
    assert "location" in result["missing_fields"]
    assert case.status == "collecting"


def test_finalize_case_changes_status_when_complete():
    case = CaseFile(
        location="123 Main Street",
        incident_type="fire",
        description="Kitchen fire",
        immediate_danger=True,
        urgency="critical",
    )

    assert case.status == "collecting"

    result = finalize_case(
        case,
        "Fire at 123 Main Street. Two people may be affected."
    )

    assert result["success"] is True
    assert result["status"] == "finalized"
    assert case.status == "finalized"

def test_execute_tool_rejects_changes_after_finalization():
    case = CaseFile(
        location="123 Main Street",
        incident_type="fire",
        description="Kitchen fire",
        immediate_danger=True,
        urgency="critical",
        status="finalized",
    )

    result = execute_tool(
        case=case,
        tool_name="update_case_field",
        arguments='{"field": "caller_name", "value": "Someone Else"}',
    )

    assert result["success"] is False
    assert "finalized case" in result["error"]
    assert case.caller_name is None



def test_finalize_case_rejects_already_finalized_case():
    case = CaseFile(
        location="123 Main Street",
        incident_type="fire",
        description="Kitchen fire",
        immediate_danger=True,
        urgency="critical",
        status="finalized",
    )

    result = finalize_case(case, "Fire at 123 Main Street.")

    assert result["success"] is False
    assert result["error"] == "Case is already finalized"
    assert case.status == "finalized"
