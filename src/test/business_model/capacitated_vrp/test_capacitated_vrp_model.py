import pytest
from src.business_model.mip.capacited_vrp_model.capacited_vrp_model import solve_cvrp
from src.data_model.cvrp_input import CVRPInput
from src.data_model.cvrp_output import CVRPOutput, TruckRoute
from src.data_model.demand import Demand
from src.data_model.truck import Truck
from src.data_model.factory import Factory
from src.data_model.demand import Demand

@pytest.fixture
def sample_cvrp_input():
    return CVRPInput(
        demands=[
            Demand(demand_id=1, weight=5, size_area=10, destination=Factory(id=1, name="A"), available_time="2024-01-01T08:00:00", due_time="2024-01-05T17:00:00"),
            Demand(demand_id=2, weight=3, size_area=5, destination=Factory(id=2, name="B"), available_time="2024-01-02T09:00:00", due_time="2024-01-06T16:00:00"),
            Demand(demand_id=3, weight=4, size_area=8, destination=Factory(id=3, name="C"), available_time="2024-01-03T10:00:00", due_time="2024-01-07T15:00:00"),
        ],
        trucks=[
            Truck(id=1, capacity=10, inner_size=15, speed=40, cost=2, type=50),
            Truck(id=2, capacity=8, inner_size=15, speed=40, cost=2, type=50),
        ],
        distance_matrix=[
            [0, 10, 15, 20],
            [10, 0, 35, 25],
            [15, 35, 0, 30],
            [20, 25, 30, 0],
        ]
    )

def test_cvrp_feasibility(sample_cvrp_input):
    output = solve_cvrp(sample_cvrp_input)

    visited_demands = set()
    for r in output.routes:
        # 1. Route starts and ends at facotory 0 (depot)
        depot = Factory(id=0, name="Depot", is_depot=True)
        assert r.route[0] == depot
        assert r.route[-1] == depot

        # 2. Load at each node does not exceed capacity
        truck_capacity = next(t.capacity for t in sample_cvrp_input.trucks if t.id == r.truck.id)
        for load in r.unload_at_node:
            assert load <= truck_capacity

        # Collect visited customer nodes (exclude depot)
        for f in r.route[1:-1]:
            visited_demands.add(f)

    # 3. All demands are visited exactly once
    all_demands = set(d.destination for d in sample_cvrp_input.demands)
    assert len(visited_demands) == len(all_demands)

    # 4. Objective value non-negative
    assert output.total_cost >= 0

def test_cvrp_no_trucks_error():
    # Should raise error if no trucks are provided
    demands = [
        Demand(demand_id=1, weight=5, size_area=10, destination=Factory(id=1, name="A"), available_time="2024-01-01T08:00:00", due_time="2024-01-05T17:00:00"),
    ]
    trucks = []
    distance_matrix = [[0, 10], [10, 0]]
    input_data = CVRPInput(demands=demands, trucks=trucks, distance_matrix=distance_matrix)

    with pytest.raises(Exception):
        solve_cvrp(input_data)
