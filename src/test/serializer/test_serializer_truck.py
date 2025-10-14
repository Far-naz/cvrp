from src.data_model.truck import Truck
from src.serializer.serializer_truck import create_truck_from_data_frame
import pandas as pd
import pytest

@pytest.fixture
def sample_truck_data_frame():
    data = {
        'Id': [1],
        'TruckTypeMeter': 120,
        'TruckSizeMeterSquared': [100],
        'CapacityPerKg': [2000],
        'CostPerKg': [150],
        'SpeedKmPerH': [80]
    }
    return pd.DataFrame(data)

def test_create_truck_from_data_frame(sample_truck_data_frame):
    trucks = create_truck_from_data_frame(sample_truck_data_frame)
    assert isinstance(trucks, dict)
    assert len(trucks) == 1

    for f in trucks.values():
        assert isinstance(f, Truck)

    truck_instance = trucks[1]
    assert truck_instance.id == 1
    assert truck_instance.type == 120
    assert truck_instance.inner_size == 100
    assert truck_instance.capacity == 2000
    assert truck_instance.cost == 150
    assert truck_instance.speed == 80