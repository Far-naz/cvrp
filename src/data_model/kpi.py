from pydantic import BaseModel

class Kpi(BaseModel):
    fix_cost: float
    service_cost: float
    total_travel_distance: float | None
    total_travel_time: float| None
    total_service_time: float  | None
    number_of_unment_orders: int | None
    total_pickup_delay_time: float | None
    total_delivery_early_time: float | None

    @property
    def total_cost(self) -> float:
        return self.fix_cost + self.service_cost
    



