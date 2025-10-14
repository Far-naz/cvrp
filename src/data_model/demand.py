from pydantic import BaseModel
from src.data_model.factory import Factory
from datetime import date, datetime, timedelta
from typing import List

class Demand(BaseModel):
    demand_id: str
    weight: float
    size_area: float
    destination: Factory
    available_time: datetime
    due_time: datetime
    travel_days: int = 0  # Number of travel days required to reach destination

    @property
    def available_date(self) -> date:
        return self.available_time.date()
    
    @property
    def available_minutes(self) -> float:
        return self.available_time.hour * 60 + self.available_time.minute
    
    @property
    def due_minutes(self) -> float:
        return self.due_time.hour * 60 + self.due_time.minute

    @property
    def due_date(self) -> date:
        return self.due_time.date()
    
    def feasible_dates(self, planning_horizon: List[date]) -> List[date]:
        """Return all feasible start dates (accounting for due_date - travel_days)."""
        td = max(1, self.travel_days)  # ensure at least 1
        last_start = self.due_date - timedelta(days=td - 1)
        return [d for d in planning_horizon if self.available_date <= d <= last_start]
        
    

    def __hash__(self):
        return hash(self.demand_id)
    
    def __eq__(self, other):
        return isinstance(other, Demand) and self.demand_id == other.demand_id
    