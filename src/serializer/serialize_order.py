from typing import Dict
import config
from src.data_model.order import Order, DangerType
import pandas as pd
from datetime import datetime
from src.data_model.factory import Factory
from src.data_model.demand import Demand
from src.utils.distance_cal import compute_travel_days


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


def get_factory_list_from_order_data_frame(
    order_data: pd.DataFrame,
) -> dict[str, Factory]:
    factory_names = set(order_data["Source"]).union(set(order_data["Destination"]))
    factories = {
        name: Factory(id=name.split("_")[1], name=name)
        for idx, name in enumerate(factory_names)
    }
    return factories


def create_factory_from_order_data(order_data: pd.DataFrame) -> dict[int, Factory]:
    factories: Dict[int, Factory] = {}
    factory_names = set(order_data["Source"]).union(set(order_data["Destination"]))
    for _, name in enumerate(factory_names):
        factory_id = int(name.split("_")[1])
        factory = Factory(
            id=factory_id,
            name=name,
            location=None,
            is_depot=(factory_id == config.DEPOT_ID),
        )
        factories[factory.id] = factory
    return factories


def create_order_from_data_frame(
    order_data: pd.DataFrame, factories: dict[str, Factory], time_format: str = config.ORDER_LARGE_DATE
) -> list[Order]:
    order_list = []
    for _, row in order_data.iterrows():
        source_factory = factories.get(row["Source"])
        destination_factory = factories.get(row["Destination"])
        try:
            available_date_local = datetime.strptime(row["Available_Time"], time_format)
            due_date_local = datetime.strptime(row["Deadline"], time_format)
        except (ValueError, TypeError):
            # Skip row if date format is incorrect or missing
            continue
        if due_date_local < available_date_local:
            continue

        danger_type = map_danger_type(row["Danger_Type"])
        order_instance = Order(
            id=row["Order_ID"],
            material_id=row["Material_ID"],
            item_id=row["Item_ID"],
            source=source_factory,
            destination=destination_factory,
            available_date_local=available_date_local,
            due_date_local=due_date_local,
            danger_type=danger_type,
            area_size=row["Area"] / 10000,
            weight=row["Weight"] / 1000000,
        )
        order_list.append(order_instance)
    return order_list


def get_demands_from_order_data_frame(
    order_data: pd.DataFrame, distances: dict[tuple[int, int], float], time_format: str = config.ORDER_LARGE_DATE
) -> list[Demand]:
    factories = get_factory_list_from_order_data_frame(order_data)
    orders = create_order_from_data_frame(order_data, factories, time_format) 
    demands: list[Demand] = []
    for order in orders:
        distance_to_destination = distances[config.DEPOT_ID][order.destination.id]
        demand = Demand(
            demand_id=order.item_id,
            weight=order.weight,
            size_area=order.area_size,
            destination=order.destination,
            available_time=order.available_date_local,
            due_time=order.due_date_local,
            travel_days=compute_travel_days(
                distance_km=distance_to_destination,
                truck_speed_kmph=40,
                unload_hours=1.0,
                load_hours=0.0,
            ),
        )
        demands.append(demand)
    return demands
