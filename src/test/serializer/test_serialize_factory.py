import pytest
from src.data_model.factory import Factory
from src.serializer.serialize_factory import create_factory_from_data_frame
import pandas as pd

@pytest.fixture
def sample_data_frame():
    data = {
        "id": [1, 2, 3],
        "name": ["Plant_1", "Warehouse_2", "Depot_3"],
        "latitude": [40.7128, 34.0522, 51.5074],
        "longitude": [-74.0060, -118.2437, -0.1278],
    }
    return pd.DataFrame(data)

def test_create_factory_from_data_frame(sample_data_frame):
    factories = create_factory_from_data_frame(sample_data_frame)


    assert isinstance(factories, dict)
    assert len(factories) == 3

    for f in factories.values():
        assert isinstance(f, Factory)

    plant_a = factories["Plant_1"]
    assert plant_a.id == 1
    assert plant_a.location == (40.7128, -74.0060)

    depot_c = factories["Depot_3"]
    assert depot_c.name == "Depot_3"
    assert isinstance(depot_c.location, tuple)

