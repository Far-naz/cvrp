import pandas as pd
import pytest
from src.data_model.factory import Factory
from src.data_model.distance import Distance
from src.serializer.serialize_distance import serialize_distance_from_data_frame


@pytest.fixture
def factories():
    return {
        "Factory A": Factory(id=0, name="Factory A"),
        "Factory B": Factory(id=1, name="Factory B"),
        "Factory C": Factory(id=2, name="Factory C"),
    }


@pytest.fixture
def distance_df():
    data = {
        "Source": ["Factory A", "Factory A", "Factory B", None, "Factory X"],
        "Destination": ["Factory B", "Factory C", "Factory C", "Factory B", "Factory A"],
        "Distance(M)": [1000, 2000, 1500, 500, 3000],
    }
    return pd.DataFrame(data)


def test_serialize_distance_from_data_frame(distance_df, factories):
    distances = serialize_distance_from_data_frame(distance_df, factories)

    assert isinstance(distances, dict)

    assert all(isinstance(k, tuple) and len(k) == 2 for k in distances.keys())
    assert all(isinstance(k[0], int) and isinstance(k[1], int) for k in distances.keys())


    assert all(isinstance(v, Distance) for v in distances.values())


    assert distances[(0, 1)].distance_m == 1000
    assert distances[(0, 2)].distance_m == 2000
    assert distances[(1, 2)].distance_m == 1500

    assert distances[(0, 1)].source.name == "Factory A"
    assert distances[(0, 1)].destination.name == "Factory B"

    assert (None, None) not in distances
    assert all(
        factories.get(distances[k].source.name) is not None and
        factories.get(distances[k].destination.name) is not None
        for k in distances.keys()
    )
