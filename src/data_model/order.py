from pydantic import BaseModel
from enum import Enum
from src.data_model.factory import Factory
from datetime import datetime, date


class DangerType(Enum):
    TYPE_1 = 0
    TYPE_2 = 1
    NOT_DANGEROUS = 3
    


class Order(BaseModel):
    id: str
    material_id: str
    item_id: str
    source: Factory
    destination: Factory
    available_date_local: datetime
    due_date_local: datetime
    danger_type: DangerType
    area_size: float
    weight: float

    @property
    def available_date(self) -> float:
        return self.available_date_local.date()
    
    @property
    def available_clock(self) -> float:
        return self.available_date_local.hour + self.available_date_local.minute / 60.0
    
    @property
    def available_date_str(self) -> str:
        return self.available_date_local.strftime('%Y-%m-%d')
    
    @property
    def due_clock(self) -> float:
        return self.due_date_local.hour + self.due_date_local.minute / 60.0

    @property
    def due_date(self) -> date:
        return self.due_date_local.date()
    
    @property
    def due_date_str(self) -> str:
        return self.due_date_local.strftime('%Y-%m-%d')
    

    def __str__(self):
        return f"Order(id={self.id})"

    