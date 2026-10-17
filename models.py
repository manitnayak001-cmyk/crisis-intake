from typing import Optional, Literal

from pydantic import BaseModel

class CaseFile(BaseModel):
    caller_name: Optional[str] = None
    callback_number: Optional[str] = None
    location: Optional[str] = None
    incident_type: Optional[str] = None
    description: Optional[str] = None
    people_affected: Optional[int] = None
    immediate_danger: Optional[bool] = None
    urgency: Optional[Literal["low", "medium", "high", "critical"]] = None
    notes: list[str] = []
    status: Literal["collecting", "finalized"] = "collecting"