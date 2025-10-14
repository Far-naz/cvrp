from pydantic import BaseModel
from src.data_model.demand import Demand
from src.data_model.truck import Truck
from typing import Dict, List
from datetime import date

class AssignmentInput(BaseModel):
    demands: List[Demand]
    trucks: List[Truck]
    planning_horizon: List[date]
    w_balance: float = 1.0
    w_slack: float = 1000.0

    # Automatically computed mappings
    @property
    def date_to_index(self) -> Dict[date, int]:
        return {d: i for i, d in enumerate(self.planning_horizon)}

    @property
    def index_to_date(self) -> Dict[int, date]:
        return {i: d for i, d in enumerate(self.planning_horizon)}

