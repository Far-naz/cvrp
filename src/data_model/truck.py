from pydantic import BaseModel

class Truck(BaseModel):
    id: int
    type: float
    inner_size: float
    capacity: float
    cost: float
    speed: float

    @property
    def travel_cost_per_km(self) -> float:
        return self.cost / self.speed

    def __str__(self):
        return f"Truck(id={self.id}, type={self.type}, inner_size={self.inner_size}, capacity={self.capacity}, cost={self.cost}, speed={self.speed})"
    
    
