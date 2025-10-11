from pydantic import BaseModel
from src.data_model.factory import Factory
from datetime import date, datetime
from typing import List

class Demand(BaseModel):
    demand_id: int
    weight: float
    size_area: float
    destination: Factory
    available_time: datetime
    due_time: datetime

    @property
    def available_date(self) -> date:
        return self.available_time.date()
    
    @property
    def due_date(self) -> date:
        return self.due_time.date()
    
    def feasible_dates(self, planning_horizon: List[date]) -> List[date]:
        """Return all dates in planning_horizon that are feasible for this demand."""
        return [d for d in planning_horizon if self.available_date <= d <= self.due_date]
    

    def __hash__(self):
        return hash(self.demand_id)
    
    def __eq__(self, other):
        return isinstance(other, Demand) and self.demand_id == other.demand_id
    