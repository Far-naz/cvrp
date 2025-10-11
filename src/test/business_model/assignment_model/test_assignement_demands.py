import pytest

from src.data_model.assignment_Input import AssignmentInput
from src.data_model.demand import Demand
from src.data_model.truck import Truck
from src.data_model.factory import Factory
from src.business_model.mip.assignment_model.assignement_demands import assign_orders
from datetime import date, timedelta, datetime
# -------------------------------
# Test datasets
# -------------------------------
start = date(2025, 10, 10)
planning_horizon = [start + timedelta(days=i) for i in range(5)]  # 10th to 14th Oct
start_datetime = datetime(2025, 10, 10)


test_cases = [
    {
        "demands": [
            Demand(demand_id=1, weight=5, size_area=10, destination=Factory(id=1, name="A"), available_time=start, due_time=planning_horizon[1]),
            Demand(demand_id=2, weight=5, size_area=20, destination=Factory(id=2, name="B"), available_time=start, due_time=planning_horizon[2]),
            Demand(demand_id=3, weight=3, size_area=15, destination=Factory(id=3, name="C"), available_time=start, due_time=planning_horizon[1]),
        ],
        "trucks": [
            Truck(id=1, capacity=3000, inner_size=15, speed=40, cost=2, type=50),
            Truck(id=2, capacity=4000, inner_size=15, speed=40, cost=2, type=50),
        ],
        "horizon": planning_horizon
            
        },
    {
        "demands": [
            Demand(demand_id=1, weight=12, size_area=5, destination=Factory(id=1, name="A", location=(0,0)), available_time=1, due_time=planning_horizon[3]),
            Demand(demand_id=2, weight=10, size_area=8, destination=Factory(id=2, name="B", location=(1,1)), available_time=2, due_time=planning_horizon[2]),
            Demand(demand_id=3, weight=8, size_area=12, destination=Factory(id=3, name="C", location=(2,2)), available_time=3, due_time=planning_horizon[1]),
            Demand(demand_id=4, weight=7, size_area=7, destination=Factory(id=4, name="D", location=(3,3)), available_time=1, due_time=planning_horizon[4]),
        ],
        "trucks": [
            Truck(id=1, capacity=2000, inner_size=15, speed=40, cost=2, type=50),
            Truck(id=2, capacity=2500, inner_size=15, speed=40, cost=2, type=50),
        ],
        "horizon": planning_horizon
        },
        
]

# -------------------------------
# Pytest parameterized test
# -------------------------------
@pytest.mark.parametrize("case", test_cases)
def test_assign_orders(case):
    demands = case["demands"]
    trucks = case["trucks"]
    horizon = case["horizon"]

    input_data = AssignmentInput(
        demands=demands,
        trucks=trucks,
        planning_horizon=horizon,
        w_balance=1,
        w_slack=1000
    )

    output = assign_orders(input_data)

    # 1. Every order is assigned exactly once
    assert len(output.assignments) == len(demands)

    # 2. Assigned days within pickup/due dates
    for a in output.assignments:
        demand = next(d for d in demands if d.demand_id == a.demand.demand_id)
        assert demand.available_date <= a.assigned_date <= demand.due_date

    # 3. Daily loads do not exceed capacity + slack
    Cap = {d: sum(t.capacity for t in trucks) for d in horizon}
    for d in horizon:
        load = output.daily_loads[d]
        slack = output.daily_slack[d]
        assert load <= Cap[d] + slack

    # 4. Objective value is non-negative
    assert output.objective_value >= 0
