import pytest
from src.data_model.factory import Factory
from src.data_model.distance import Distance


def test_distance_initialization():
    source_factory = Factory(id=1, name="Factory A", location=(12.34, 56.78))
    destination_factory = Factory(id=2, name="Factory B", location=(98.76, 54.32))
    
    distance_instance = Distance(
        source=source_factory,
        destination=destination_factory,
        distance_m=1500.0
    )
    
    assert distance_instance.source == source_factory
    assert distance_instance.destination == destination_factory
    assert distance_instance.distance_m == 1500.0

def test_distance_in_km():
    assert Distance.distance_in_km(1500.0) == 1.5
    assert Distance.distance_in_km(0.0) == 0.0
    assert Distance.distance_in_km(10000.0) == 10.0

