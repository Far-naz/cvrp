import pandas as pd
import pytest
from src.data_model.factory import Factory
from src.data_model.distance import Distance
from src.serializer.serialize_distance import serialize_distance_from_data_frame


@pytest.fixture
def factories():
    return {
        "Factory_1": Factory(id=0, name="Factory_1"),
        "Factory_2": Factory(id=1, name="Factory_2"),
        "Factory_3": Factory(id=2, name="Factory_3"),
    }


@pytest.fixture
def distance_df():
    data = {
        "Source": ["Factory_1", "Factory_1", "Factory_2", "Factory_3", "Factory_3"],
        "Destination": ["Factory_2", "Factory_3", "Factory_3", "Factory_2", "Factory_1"],
        "Distance(M)": [1000, 2000, 1500, 500, 3000],
    }
    return pd.DataFrame(data)


def test_serialize_distance_from_data_frame(distance_df, factories):
    distances = serialize_distance_from_data_frame(distance_df, factories)

    assert isinstance(distances, dict)

    assert all(isinstance(k, tuple) and len(k) == 2 for k in distances.keys())
    assert all(isinstance(k[0], int) and isinstance(k[1], int) for k in distances.keys())


    assert all(isinstance(v, Distance) for v in distances.values())

    assert (None, None) not in distances
    assert all(
        factories.get(distances[k].source.name) is not None and
        factories.get(distances[k].destination.name) is not None
        for k in distances.keys()
    )
