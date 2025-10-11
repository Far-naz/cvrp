import pytest
from src.data_model.factory import Factory

def test_factory_initialization():
    factory_instance = Factory(id=1, name="Factory A", location=(12.34, 56.78))
    assert factory_instance.id == 1
    assert factory_instance.name == "Factory A"
    assert factory_instance.location == (12.34, 56.78)

def test_empty_location():
    factory_instance = Factory(id=2, name="Factory B")
    assert factory_instance.id == 2
    assert factory_instance.name == "Factory B"
    assert factory_instance.location is None

def test_factory_str_representation():
    factory_instance = Factory(id=1, name="Factory A", location=(12.34, 56.78))
    expected_str = "Factory(id=1, name=Factory A,)"
    assert str(factory_instance) == expected_str