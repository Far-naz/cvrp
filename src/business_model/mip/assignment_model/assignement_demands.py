import gurobipy as gp
from gurobipy import GRB
from src.data_model.assignment_Input import AssignmentInput
from src.data_model.assignment_output import AssignmentOutput
from src.data_model.assignment_demand import OrderAssignment
from src.data_model.demand import Demand
from typing import List

def compute_daily_capacity(trucks, planning_horizon):
    Cap = {d: 0.0 for d in planning_horizon}
    for truck in trucks:
        for d in planning_horizon:
            Cap[d] += truck.capacity
    return Cap

def assign_orders(input_data: AssignmentInput) -> AssignmentOutput:
    demands: List[Demand] = input_data.demands
    planning_horizon = input_data.planning_horizon
    trucks = input_data.trucks
    w_bal = input_data.w_balance
    w_slack = input_data.w_slack

    planning_horizon_range = range(len(planning_horizon))

    # Compute total capacity per day
    Cap = compute_daily_capacity(trucks, planning_horizon_range)
    
    # Average load for balance
    AvgLoad = sum(d.weight for d in demands) / len(planning_horizon)

    demand_ids = [d.demand_id for d in demands]
    
    date_to_index = {d: i for i, d in enumerate(planning_horizon)}
    index_to_date = {i: d for d, i in date_to_index.items()}

    # Initialize model
    m = gp.Model("Order_Assignment")

    # Decision variables
    x = m.addVars(demand_ids, planning_horizon_range, vtype=GRB.BINARY, name="x")
    Load = m.addVars(planning_horizon_range, lb=0, name="l")
    z = m.addVars(planning_horizon_range, lb=0, name="z")
    slack = m.addVars(planning_horizon_range, lb=0, name="s")

    # Each order assigned exactly once
    m.addConstrs(gp.quicksum(x[d.demand_id, t] for t in planning_horizon_range) == 1 for d in demands)

    # Pickup/due date feasibility
    for o in demands:
        feasible_days = [date_to_index[d] for d in o.feasible_dates(planning_horizon)]
        for t in range(len(planning_horizon)):
            if t not in feasible_days:
                x[o.demand_id, t].ub = 0

    # Define daily loads
    m.addConstrs((Load[d] == gp.quicksum(o.weight*x[o.demand_id,d] for o in demands) for d in planning_horizon_range), name="load_def")

    # Capacity (with slack)
    m.addConstrs((Load[d] <= Cap[d] + slack[d] for d in planning_horizon_range), name="capacity")

    # Balance deviation
    m.addConstrs((z[d] >= Load[d] - AvgLoad for d in planning_horizon_range), name="pos_dev")
    m.addConstrs((z[d] >= AvgLoad - Load[d] for d in planning_horizon_range), name="neg_dev")

    # Objective
    m.setObjective(w_bal * gp.quicksum(z[d] for d in planning_horizon_range) +
                   w_slack * gp.quicksum(slack[d] for d in planning_horizon_range),
                   GRB.MINIMIZE)

    # Solve
    m.optimize()

    # Extract results
    assignments = []
    daily_loads = {}
    daily_slack = {}
    daily_balance = {}

    if m.status == GRB.OPTIMAL:
        for o in demands:
            for t in range(len(planning_horizon)):
                if x[o.demand_id, t].x > 0.5:
                    assignments.append(
                        OrderAssignment(
                            demand=o,
                            assigned_date=index_to_date[t]
                        )
                    )
        for d in planning_horizon_range:
            daily_loads[index_to_date[d]] = Load[d].x
            daily_slack[index_to_date[d]] = slack[d].x
            daily_balance[index_to_date[d]] = z[d].x

        return AssignmentOutput(
            assignments=assignments,
            daily_loads=daily_loads,
            daily_slack=daily_slack,
            daily_balance=daily_balance,
            objective_value=m.objVal
        )
    else:
        raise Exception("No optimal solution found")
