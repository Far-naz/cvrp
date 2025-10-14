from pydantic import BaseModel
from src.data_model.assignment_demand import OrderAssignment
from typing import List, Dict
from datetime import date

class AssignmentOutput(BaseModel):
    assignments: List[OrderAssignment]
    daily_loads: Dict[date, float]
    daily_areas: Dict[date, float] | None = None
    daily_slack: Dict[date, float] | None = None
    daily_balance: Dict[date, float] | None = None
    objective_value: float | None = None
    is_success: bool = True