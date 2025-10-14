import pandas as pd
from datetime import datetime
import pytest
from src.data_model.order import Order, DangerType
from src.data_model.factory import Factory
from src.serializer.serialize_order import create_order_from_data_frame,get_factory_list_from_order_data_frame


@pytest.fixture
def factories():
    return {
        "Factory_1": Factory(id=1, name="Factory_1", location=(40.7128, -74.0060)),
        "Factory_2": Factory(id=2, name="Factory_2", location=(34.0522, -118.2437)),
    }


@pytest.fixture
def order_df():
    data = {
        "Order_ID": ["1"],
        "Material_ID": ["101"],
        "Item_ID": ["500"],
        "Source": ["Factory_1"],
        "Destination": ["Factory_2"],
        "Available_Time": ["4/5/2022 23.59"],
        "Deadline": ["4/11/2022 23.59"],
        "Danger_Type": ['type_1'],
        "Area": [15.5],
        "Weight": [120.0],
    }
    return pd.DataFrame(data)


def test_create_order_from_data_frame(order_df, factories):
    orders = create_order_from_data_frame(order_df, factories)

    assert isinstance(orders, list)
    assert len(orders) == 1
    order = orders[0]

    assert isinstance(order, Order)
    assert isinstance(order.available_date_local, datetime)
    assert isinstance(order.due_date_local, datetime)

    assert order.available_date == datetime(2022, 5, 4).date()
    assert order.due_date == datetime(2022, 11, 4).date()

    assert order.source.name == "Factory_1"
    assert order.destination.name == "Factory_2"


    assert order.area_size == 15.5 / 10000
    assert order.weight == 120.0 /1000000


    assert order.danger_type == DangerType.TYPE_1



def test_get_factory_list_from_order_data_frame():
    data = {
        "Source": ["Factory_1", "Factory_2", "Factory_3"],
        "Destination": ["Factory_2", "Factory_4", "Factory_1"],
        "Material_ID": ["1", "2", "3"],
    }
    df = pd.DataFrame(data)

    factories = get_factory_list_from_order_data_frame(df)

    assert isinstance(factories, dict)
    assert all(isinstance(v, Factory) for v in factories.values())

    expected_names = {"Factory_1", "Factory_2", "Factory_3", "Factory_4"}
    assert set(factories.keys()) == expected_names

 
    for name, factory in factories.items():
        assert factory.name == name

    ids = [f.id for f in factories.values()]
    assert len(ids) == len(set(ids))
    assert all(isinstance(i, int) for i in ids)

    assert min(ids) == 1
    assert max(ids) == 4
