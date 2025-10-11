from pydantic import BaseModel
from src.data_model.assignment_demand import OrderAssignment
from typing import List, Dict
from datetime import date

class AssignmentOutput(BaseModel):
    assignments: List[OrderAssignment]
    daily_loads: Dict[date, float]
    daily_slack: Dict[date, float]
    daily_balance: Dict[date, float]
    objective_value: float