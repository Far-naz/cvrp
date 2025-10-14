from src.data_model.truck import Truck
import pandas as pd
from typing import Dict


def create_truck_from_data_frame(df: pd.DataFrame) -> Dict[str,Truck]:
    truck_list: Dict[str, Truck] = {}
    for _, row in df.iterrows():
        truck_instance = Truck(
            id=row['Id'],
            type=row['TruckTypeMeter'],
            inner_size=row['TruckSizeMeterSquared'],
            capacity=row['CapacityPerKg'],
            cost=row['CostPerKg'],
            speed=row['SpeedKmPerH']
        )
        truck_list[truck_instance.id] = truck_instance
    return truck_list
