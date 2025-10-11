import pytest
from src.data_model.truck import Truck


def test_truck_initialization():
    truck = Truck(id=1, type=2.0, inner_size=10.0, capacity=5.0, cost=100.0, speed=60.0)
    assert truck.id == 1
    assert truck.type == 2.0
    assert truck.inner_size == 10.0
    assert truck.capacity == 5.0
    assert truck.cost == 100.0
    assert truck.speed == 60.0


def test_truck_str_representation():
    truck = Truck(id=1, type=2.0, inner_size=10.0, capacity=5.0, cost=100.0, speed=60.0)
    expected_str = "Truck(id=1, type=2.0, inner_size=10.0, capacity=5.0, cost=100.0, speed=60.0)"
    assert str(truck) == expected_str

