import pytest

from agents.tools import update_case_field
from models import CaseFile


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