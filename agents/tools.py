from models import CaseFile

def update_case_field(
        case: CaseFile,
        field: str,
        value: str,
):
    if not hasattr(case, field): #checks if the field is present in case or not
        raise ValueError(f"Invalid field: {field}")
    setattr(case, field, value)

    return {
        "success": True,
        "field": field,
        "value": value,
    }


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "update_case_field",
            "description": (
                "Record a fact the caller stated. "
                "Only use information the caller actually provided."
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
                        "type": "string",
                    },
                },
                "required": ["field", "value"],
            },
        },
    }
]