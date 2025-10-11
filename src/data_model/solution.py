from pydantic import BaseModel
from src.data_model.service import Service
from src.data_model.kpi import Kpi

class Solution(BaseModel):
    services: list[Service]
    kpi: Kpi
    