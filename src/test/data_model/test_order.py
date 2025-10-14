import pytest
from src.data_model.factory import Factory
from src.data_model.order import Order, DangerType
from datetime import datetime

def test_order_initialization():
    source_factory = Factory(id=1, name="Factory A", location=(12.34, 56.78))
    destination_factory = Factory(id=2, name="Factory B", location=(98.76, 54.32))
    
    available_date_local = datetime(2021, 6, 1, 10, 0)
    due_date_local = datetime(2021, 7, 1, 10, 0)

    order_instance = Order(
        id="100",
        material_id="200",
        item_id="300",
        source=source_factory,
        destination=destination_factory,
        available_date_local=available_date_local,
        due_date_local=due_date_local,
        danger_type=DangerType.TYPE_2,
        area_size=50.0,
        weight=1000.0
    )
    
    assert order_instance.id == "100"
    assert order_instance.material_id == "200"
    assert order_instance.item_id == "300"
    assert order_instance.source == source_factory
    assert order_instance.destination == destination_factory
    assert order_instance.available_date_local == available_date_local
    assert order_instance.due_date_local == due_date_local
    assert order_instance.available_date == available_date_local.date()
    assert order_instance.due_date == due_date_local.date()
    assert order_instance.danger_type == DangerType.TYPE_2
    assert order_instance.area_size == 50.0
    assert order_instance.weight == 1000.0

def test_order_str_representation():
    source_factory = Factory(id=1, name="Factory A", location=(12.34, 56.78))
    destination_factory = Factory(id=2, name="Factory B", location=(98.76, 54.32))
    
    order_instance = Order(
        id="100",
        material_id="200",
        item_id="300",
        source=source_factory,
        destination=destination_factory,
        available_date_local=1622548800.0,
        due_date_local=1625130800.0,
        danger_type=1,
        area_size=50.0,
        weight=1000.0
    )
    
    expected_str = "Order(id=100"
    assert str(order_instance).startswith(expected_str)