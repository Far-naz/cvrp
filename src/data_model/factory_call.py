from src.data_model.factory import Factory
from src.data_model.order import Order
from datetime import datetime
from pydantic import BaseModel

class FactoryCall(BaseModel):
    factory : Factory
    arrival_time :datetime
    departure_time : datetime
    pickup_orders: list[Order]
    delivery_orders: list[Order]
    
    @property
    def service_cost(self) -> float:
        if len(self.delivery_orders) > 0:
            return sum(self.delivery_orders)*1
        
    @property
    def service_time(self) -> float:
        return (self.departure_time - self.arrival_time).total_seconds() / 3600
