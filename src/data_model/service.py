from pydantic import BaseModel
from src.data_model.factory_call import FactoryCall
from src.data_model.truck import Truck
from datetime import datetime

class Service(BaseModel):
    id: int
    factories: list[FactoryCall]
    start_time_depot: datetime
    end_time_depot: datetime
    fixed_cost: float
    variable_cost: float
    truck: Truck


    @property
    def total_cost(self) -> float:
        return self.fixed_cost + self.variable_cost
    
    @property
    def total_delivery_orders(self) -> int:
        return sum(len(fc.delivery_orders) for fc in self.factories)
    
    @property
    def total_pickup_orders(self) -> int:
        return sum(len(fc.pickup_orders) for fc in self.factories)
    
    @property
    def total_orders(self) -> int:
        return self.total_delivery_orders + self.total_pickup_orders
    
    @property
    def total_used_capacity(self) -> float:
        return sum(order.size_kg for fc in self.factories for order in fc.pickup_orders + fc.delivery_orders)   
    
    @property
    def total_truck_capacity_empty(self) -> float:
        return self.truck.capacity - self.total_used_capacity
    
    @property
    def total_truck_area_used(self)-> float:
        return sum(order.area_m2 for fc in self.factories for order in fc.pickup_orders + fc.delivery_orders)
    
    @property
    def total_truck_area_empty(self) -> float:
        return self.truck.inner_size - self.total_truck_area_used
    
