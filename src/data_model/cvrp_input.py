from pydantic import BaseModel
from typing import List
from src.data_model.demand import Demand
from src.data_model.truck import Truck

class CVRPInput(BaseModel):
    demands: List[Demand]
    trucks: List[Truck]
    distance_matrix: List[List[float]]