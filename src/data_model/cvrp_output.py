from pydantic import BaseModel
from typing import List
from src.data_model.truck import Truck
from src.data_model.factory import Factory

class TruckRoute(BaseModel):
    truck: Truck
    route: List[Factory]
    unload_at_node: List[float]

class CVRPOutput(BaseModel):
    routes: List[TruckRoute]
    total_cost: float