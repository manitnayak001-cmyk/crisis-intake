from models import CaseFile
import json

STRING_FIELDS = {
    "caller_name",
    "callback_number",
    "location",
    "incident_type",
    "description",
}


def update_case_field(
    case: CaseFile,
    field: str,
    value,
):
    if field not in STRING_FIELDS and field not in {
        "people_affected",
        "immediate_danger",
    }:
        raise ValueError(f"Unknown case field: {field}")

    if field in STRING_FIELDS and not isinstance(value, str):
        raise ValueError(f"Field '{field}' must be a string")
    if field == "people_affected" and type(value) is not int:
        raise ValueError("Field 'people_affected' must be an integer")
    if field == "immediate_danger" and type(value) is not bool:
        raise ValueError("Field 'immediate_danger' must be a boolean")

    setattr(case, field, value)

    return {
        "success": True,
        "field": field,
        "value": getattr(case, field),
    }


REQUIRED_FIELDS = [
    "location",
    "incident_type",
    "description",
    "immediate_danger",
    "urgency",
    "people_affected",
]

def check_completeness(case: CaseFile):
    missing_fields = []

    for field in REQUIRED_FIELDS:
        value = getattr(case, field)
        if value is None:
            missing_fields.append(field)

    return {
        "complete": len(missing_fields) == 0,
        "missing_fields": missing_fields,
    }

def is_case_complete(case: CaseFile) -> bool:
    return check_completeness(case)["complete"]


def flag_urgency(case: CaseFile, level: str, reason: str):
    allowed_levels = ["low", "medium", "high", "critical"]
    if level not in allowed_levels:
        raise ValueError(f"Invalid urgency level: {level}")
    
    case.urgency = level
    case.notes.append(f"Urgency flagged as {level}: {reason}")
    return {
        "success": True,
        "level": level,
        "reason": reason,
    }

def finalize_case(case: CaseFile, summary: str):
    # Guard against repeated finalization.
    if case.status == "finalized":
        return {
            "success": False,
            "error": "Case is already finalized",
        }
    completeness = check_completeness(case)

    if not completeness["complete"]:
        return {
            "success": False,
            "error": "Cannot finalize incomplete case",
            "missing_fields": completeness["missing_fields"],
        }

    case.status = "finalized"

    return {
        "success": True,
        "status": case.status,
        "summary": summary,
    }

def execute_tool(case: CaseFile, tool_name: str, arguments: str):
    if case.status == "finalized":
        return {
            "success": False,
            "error": "Cannot execute tools on a finalized case",
        }

    args = json.loads(arguments)
    if tool_name == "update_case_field":
        return update_case_field(case, **args)
    if tool_name == "flag_urgency":
        return flag_urgency(case, **args)
    if tool_name == "check_completeness":
        return check_completeness(case)
    if tool_name == "finalize_case":
        return finalize_case(case, **args)
    raise ValueError(f"Unknown tool: {tool_name}")



TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "update_case_field",
            "description": (
                "Record a fact the caller explicitly provided. "
                "Use only information actually stated by the caller. "
                "Field types are: "
                "caller_name, callback_number, location, "
                "incident_type, and description are strings; "
                "people_affected is an integer; "
                "immediate_danger is a boolean."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "enum": [
                            "caller_name",
                            "callback_number",
                            "location",
                            "incident_type",
                            "description",
                            "people_affected",
                            "immediate_danger",
                        ],
                    },
                    "value": {
                        "type": ["string", "integer", "boolean"],
                    },
                },
                "required": ["field", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "flag_urgency",
            "description": (
                "Set the urgency level when the caller's situation "
                "indicates a potential safety risk. Always provide "
                "a brief reason based only on information the caller "
                "actually provided."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "enum": [
                            "low",
                            "medium",
                            "high",
                            "critical",
                        ],
                    },
                    "reason": {
                        "type": "string",
                    },
                },
                "required": [
                    "level",
                    "reason",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_completeness",
            "description": (
                "Check whether all required case fields have been collected. "
                "Returns the required fields that are still missing."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finalize_case",
            "description": (
                "Finalize the case if all required fields have been collected. "
                "Provide a brief summary of the case."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                    },
                },
                "required": ["summary"],
            },
        },
    }
]