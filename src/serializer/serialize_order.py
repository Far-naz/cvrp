from src.data_model.order import Order, DangerType
import pandas as pd
from datetime import datetime
from src.data_model.factory import Factory
from src.data_model.demand import Demand

def map_danger_type(value: str) -> DangerType:
    key = str(value).strip().lower()
    mapping = {
        "type_1": DangerType.TYPE_1,
        "type_2": DangerType.TYPE_2,
        "non_danger": DangerType.NOT_DANGEROUS,
    }
    if key not in mapping:
        raise ValueError(f"Invalid danger type: {value}")
    return mapping[key]

def get_factory_list_from_order_data_frame(order_data:pd.DataFrame)->dict[str, Factory]:
    factory_names = set(order_data['Source']).union(set(order_data['Destination']))
    factories = {name: Factory(id=idx, name=name) for idx, name in enumerate(factory_names)}
    return factories

def create_order_from_data_frame(order_data: pd.DataFrame, factories: dict[str, Factory]) -> list[Order]:
    order_list = []
    for _, row in order_data.iterrows():
        source_factory = factories.get(row["Source"])
        destination_factory = factories.get(row["Destination"]) 
        available_date_local = datetime.strptime(row['Available_Time'], '%d/%m/%y %H:%M')
        due_date_local = datetime.strptime(row['Deadline'], '%d/%m/%y %H:%M')
        danger_type = map_danger_type(row['Dangerous'])
        order_instance = Order(
            id=row['Order_ID'],
            material_id=row['Material_ID'],
            item_id=row['Item_ID'],
            source=source_factory,
            destination=destination_factory,
            available_date_local=available_date_local,
            due_date_local=due_date_local,
            danger_type=danger_type,
            area_size=row['Area'],
            weight=row['Weight'] / 100000
        )
        order_list.append(order_instance)
    return order_list

def get_demands_from_order_data_frame(order_data: pd.DataFrame) -> list[Demand]:
    factories = get_factory_list_from_order_data_frame(order_data)
    orders = create_order_from_data_frame(order_data, factories)
    demands = [
        Demand(
            demand_id=order.item_id,
            weight=order.weight,
            size_area=order.area_size,
            destination=order.destination,
            available_time=order.available_date_local,
            due_time=order.due_date_local
        ) for order in orders
    ]
    return demands