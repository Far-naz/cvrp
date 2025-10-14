from pydantic import BaseModel
from typing import List
from src.data_model.truck import Truck
from src.data_model.factory import Factory

class TruckRoute(BaseModel):
    truck: Truck
    route: List[Factory]
    unload_at_node: List[float]
    times_at_node: List[str] | None = None
    travel_times_at_node: List[float] | None = None
    travel_distance: float | None = None
    travel_time: float | None = None
    total_stops: int | None = None
    total_travel_cost: float | None = None
    total_handling_cost: float | None = None


    @property
    def total_weight(self) -> float:
        return sum(truck_route.truck.capacity_weight for truck_route in self.routes)
    
    @property
    def total_volume(self) -> float:
        return sum(truck_route.truck.capacity_volume for truck_route in self.routes)
    


class CVRPOutput(BaseModel):
    routes: List[TruckRoute]
    total_cost: float
    travel_cost: float | None = None
    handling_cost: float | None = None
    is_success: bool = True