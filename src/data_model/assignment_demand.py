from pydantic import BaseModel
from src.data_model.demand import Demand
from src.data_model.truck import Truck
from datetime import date

class OrderAssignment(BaseModel):
    demand: Demand
    assigned_date: date
    truck: Truck|None

    def __eq__(self, other):
        if not isinstance(other, OrderAssignment):
            return False
        return (self.demand == other.demand and
                self.assigned_date == other.assigned_date)

    def __hash__(self):
        return hash((self.demand, self.assigned_date))