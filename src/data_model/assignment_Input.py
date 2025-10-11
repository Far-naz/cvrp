from pydantic import BaseModel
from src.data_model.demand import Demand
from src.data_model.truck import Truck
from typing import List
from datetime import date

class AssignmentInput(BaseModel):
    demands: List[Demand]
    trucks: List[Truck]
    planning_horizon: List[date]
    w_balance: float = 1.0
    w_slack: float = 1000.0


