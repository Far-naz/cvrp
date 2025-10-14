import gurobipy as gp
from gurobipy import GRB
from networkx import config
from src.data_model.assignment_demand import OrderAssignment
from src.data_model.assignment_Input import AssignmentInput
from src.data_model.assignment_output import AssignmentOutput
from src.data_model.demand import Demand
from src.data_model.truck import Truck
from datetime import date, datetime
from typing import List, Dict
from collections import defaultdict
import config


def _build_date_index_maps(
    planning_horizon: List[date],
) -> tuple[Dict[date, int], Dict[int, date]]:
    """
    Build mappings between planning dates and their integer indices.
    Useful for Gurobi or NumPy indexing.
    """
    date_to_index = {d: i for i, d in enumerate(planning_horizon)}
    index_to_date = {i: d for i, d in enumerate(planning_horizon)}
    return date_to_index, index_to_date


def assign_orders_with_truck(input_data: AssignmentInput) -> AssignmentOutput:
    demands: list[Demand] = input_data.demands
    trucks: list[Truck] = input_data.trucks
    planning_horizon: list[date] = input_data.planning_horizon
    w_balance: float = input_data.w_balance
    w_slack: float = input_data.w_slack

    H = len(planning_horizon)
    planning_horizon_range = range(H)

    # Compute average load per day (for balance)
    total_weight = sum(d.weight for d in demands)
    AvgLoad = total_weight / H
    demand_ids = [d.demand_id for d in demands]
    truck_ids = [t.id for t in trucks]

    date_to_index, index_to_date = _build_date_index_maps(planning_horizon)

    dest_to_demands = defaultdict(list)
    for d in demands:
        dest_to_demands[d.destination].append(d)

    m = gp.Model("AssignOrders_Truck")

    # Decision variable x[i,t,k] = 1 if demand i assigned to truck k starting on day t
    triples = (
        (d.demand_id, date_to_index[fd], k_id)
        for d in demands
        for fd in d.feasible_dates(planning_horizon)
        for k_id in truck_ids
    )
    x = m.addVars(triples, vtype=GRB.BINARY, name="x")
    # Daily total load and balance vars
    Load = m.addVars(planning_horizon_range, lb=0, name="Load")
    z = m.addVars(planning_horizon_range, lb=0, name="BalanceDeviation")
    slack = m.addVars(planning_horizon_range, lb=0, name="Slack")

    # Each demand assigned exactly once (across all trucks and dates)
    infeasible_demands = []
    for d in demands:
        feasible_dates = d.feasible_dates(planning_horizon)
        feasible_idxs = [date_to_index[fd] for fd in feasible_dates]
        if not feasible_idxs:
            infeasible_demands.append(d.demand_id)
            continue
        m.addConstr(
            gp.quicksum(
                x[d.demand_id, t_idx, k_id]
                for t_idx in feasible_idxs
                for k_id in truck_ids
            )
            == 1,
            name=f"assign_once_{d.demand_id}",
        )


    for day_idx in planning_horizon_range:
        day_date = index_to_date[day_idx]
        expr = gp.quicksum(
            d.weight * x[d.demand_id, s_idx, k_id]
            for d in demands
            for s in d.feasible_dates(planning_horizon)
            for s_idx in [date_to_index[s]]
            for k_id in truck_ids
            if s_idx <= day_idx < s_idx + d.travel_days
        )
        m.addConstr(Load[day_idx] == expr, name=f"load_active_{day_idx}")

    for t in trucks:
        for day_idx in planning_horizon_range:
            expr_weight = gp.quicksum(
                d.weight * x[d.demand_id, s_idx, t.id]
                for d in demands
                for s in d.feasible_dates(planning_horizon)
                for s_idx in [date_to_index[s]]
                if s_idx <= day_idx < s_idx + d.travel_days
            )
            expr_size = gp.quicksum(
                d.size_area * x[d.demand_id, s_idx, t.id]
                for d in demands
                for s in d.feasible_dates(planning_horizon)
                for s_idx in [date_to_index[s]]
                if s_idx <= day_idx < s_idx + d.travel_days
            )
            m.addConstr(expr_weight <= t.capacity, name=f"truckcap_{t.id}_{day_idx}")
            m.addConstr(
                expr_size <= t.inner_size, name=f"size_cap_truck_{t.id}_{day_idx}"
            )

    for day in planning_horizon_range:
        m.addConstr(Load[day] - AvgLoad <= z[day], name=f"pos_dev_{day}")
        m.addConstr(AvgLoad - Load[day] <= z[day], name=f"neg_dev_{day}")

    for t in trucks:
        for s_idx in planning_horizon_range:
            m.addConstr(
                gp.quicksum(
                    gp.quicksum(
                        x[d.demand_id, s_idx, t.id]
                        for d in dest_to_demands[dest]
                        if s_idx in [date_to_index[s] for s in d.feasible_dates(planning_horizon)]
                    ) / len(dest_to_demands[dest])
                    for dest in dest_to_demands
                )
                <= config.MAX_STOPS,
                name=f"approx_maxstops_{t.id}_{s_idx}",
            )

    m.setObjective(
        w_balance * gp.quicksum(z[d] for d in planning_horizon_range)
        + w_slack * gp.quicksum(slack[d] for d in planning_horizon_range),
        GRB.MINIMIZE,
    )

    m.params.OutputFlag = 0  # display solver output
    m.params.TimeLimit = 1800  # 30 minutes

    m.optimize()

    # Extract results
    assignments = []
    daily_loads = {}
    daily_slack = {}
    daily_balance = {}

    # --- Extract solution ---
    if m.status == GRB.OPTIMAL:
        for d in demands:
            for s in d.feasible_dates(planning_horizon):
                s_idx = date_to_index[s]
                for k in trucks:
                    if x[d.demand_id, s_idx, k.id].X > 0.5:
                        oa = OrderAssignment(
                            demand=d,
                            assigned_date=index_to_date[s_idx],
                            truck=k,
                        )

                        assignments.append(oa)

        daily_loads: Dict = {date: 0.0 for date in planning_horizon}
        for oa in assignments:
            d_obj: Demand = oa.demand
            start_idx = date_to_index[oa.assigned_date]
            for day_offset in range(d_obj.travel_days):
                idx = start_idx + day_offset
                if idx < H:
                    day_date = index_to_date[idx]
                    daily_loads[day_date] += d_obj.weight

        # total capacity per calendar day (test expects sum of truck capacities)
        total_capacity_per_day = sum(t.capacity for t in trucks)
        daily_slack = {
            date: max(0.0, total_capacity_per_day - load)
            for date, load in daily_loads.items()
        }

        # daily balance = abs(Load - AvgLoad) -- compute from daily_loads
        daily_balance = {
            date: abs(load - AvgLoad) for date, load in daily_loads.items()
        }

        # total weight of each truck used (for info)
        truck_loads = {t.id: 0.0 for t in trucks}
        for oa in assignments:
            truck_loads[oa.truck.id] += oa.demand.weight
        # print truck loads
        for t in trucks:
            print(
                f"Truck {t.id} total assigned weight: {truck_loads[t.id]} / {t.capacity}"
            )

        # total truck size used for each day
        truck_sizes = {t.id: 0.0 for t in trucks}
        for oa in assignments:
            truck_sizes[oa.truck.id] += oa.demand.size_area
        # print truck sizes
        for t in trucks:
            print(
                f"Truck {t.id} total assigned size: {truck_sizes[t.id]} / {t.inner_size}"
            )

        # available trucks in each day (for info)
        for day in planning_horizon_range:
            available_trucks = sum(
                1
                for t in trucks
                if any(
                    x[d.demand_id, day, t.id].X > 0.5
                    for d in demands
                    if day
                    in [date_to_index[fd] for fd in d.feasible_dates(planning_horizon)]
                )
            )
            print(f"Day {index_to_date[day]}: {available_trucks} trucks used.")

        # Objective value
        objective_value = m.objVal

        # Build and return AssignmentOutput
        result = AssignmentOutput(
            assignments=assignments,
            daily_loads=daily_loads,
            daily_slack=daily_slack,
            daily_balance=daily_balance,
            objective_value=objective_value,
            is_success=True,
        )

        return result
    else:
        return AssignmentOutput(
            assignments=[],
            daily_loads={},
            daily_slack={},
            daily_balance={},
            objective_value=0.0,
            is_success=False,
        )



def assignment_orders_to_trucks_days(input_data: AssignmentInput) -> AssignmentOutput:
    demands: list[Demand] = input_data.demands
    trucks: list[Truck] = input_data.trucks
    planning_horizon: list[date] = input_data.planning_horizon
    w_balance: float = input_data.w_balance
    w_slack: float = input_data.w_slack

    H = len(planning_horizon)
    planning_horizon_range = range(H)

    # Compute average load per day (for balance)
    total_weight = sum(d.weight for d in demands)
    AvgLoad = total_weight / H
    truck_ids = [t.id for t in trucks]

    date_to_index, index_to_date = _build_date_index_maps(planning_horizon)

    dest_to_demands = defaultdict(list)
    for d in demands:
        dest_to_demands[d.destination].append(d)

    # Build model
    m = gp.Model("AssignOrders_Truck")

    # Decision variable x is 1 if demand i assigned to truck k starting on day t
    triples = (
        (d.demand_id, date_to_index[fd], k_id)
        for d in demands
        for fd in d.feasible_dates(planning_horizon)
        for k_id in truck_ids
    )
    x = m.addVars(triples, vtype=GRB.BINARY, name="x")
    
    # u 1 if truck 𝑘 visits destination i on day d
    unique_dest_ids = list({d.destination.id for d in demands})
    u = m.addVars(
        unique_dest_ids,
        planning_horizon_range,
        truck_ids,
        name="u",
        lb=0,
        ub=1,
    )

    # Daily total load and balance vars
    Load = m.addVars(planning_horizon_range, lb=0, name="Load")
    # Truck k used on day t
    y = m.addVars(len(planning_horizon), [t.id for t in trucks], vtype=GRB.BINARY, name="y")

    # --- constraints ---
    # 1. Every item assigned exactly once
    for d in demands:
        feasible_idxs = [date_to_index[fd] for fd in d.feasible_dates(planning_horizon)]
        m.addConstr(
            gp.quicksum(
                x[d.demand_id, t_idx, k_id]
                for t_idx in feasible_idxs
                for k_id in truck_ids
            )
            == 1,
        )

    # 2. truck-day capacity and size constraints
    for t in trucks:
        for day_idx in planning_horizon_range:
            expr_weight = gp.quicksum(
                d.weight * x[d.demand_id, s_idx, t.id]
                for d in demands
                for s_idx in [
                    date_to_index[s] for s in d.feasible_dates(planning_horizon)
                ]
                if s_idx <= day_idx < s_idx + d.travel_days
            )
            expr_size = gp.quicksum(
                d.size_area * x[d.demand_id, s_idx, t.id]
                for d in demands
                for s_idx in [
                    date_to_index[s] for s in d.feasible_dates(planning_horizon)
                ]
                if s_idx <= day_idx < s_idx + d.travel_days
            )
            m.addConstr(expr_weight <= t.capacity)
            m.addConstr(expr_size <= t.inner_size)

    # total load of truck k on day d
    for day_idx in planning_horizon_range:
        expr_weight = gp.quicksum(
            d.weight * x[d.demand_id, s_idx, t.id]
            for d in demands
            for s_idx in [
                date_to_index[s] for s in d.feasible_dates(planning_horizon)
            ]
            if s_idx <= day_idx < s_idx + d.travel_days
            for t in trucks
        )
    m.addConstr(Load[day_idx] == expr_weight)

    # 3) item stop coupling
    for d in demands:
        dest = d.destination.id
        feasible_idxs = [date_to_index[fd] for fd in d.feasible_dates(planning_horizon)]
        for t_idx in feasible_idxs:
            for k_id in truck_ids:
                m.addConstr(u[dest, t_idx, k_id] >= x[d.demand_id, t_idx, k_id])

    # 5. Max stops per truck per day
    for t_id in truck_ids:
        for t_idx in planning_horizon_range:
            destinations_that_day = list({d.destination.id for d in demands})
            m.addConstr(
                gp.quicksum(u[dest, t_idx, t_id] for dest in destinations_that_day)
                <= config.MAX_STOPS
            )
    
    # 6. availability of trucks
    for t in trucks:
        for d in demands:
            for s in d.feasible_dates(planning_horizon):
                s_idx = date_to_index[s]
                for day_idx in range(s_idx, min(s_idx + d.travel_days, len(planning_horizon))):
                    m.addConstr(
                        y[day_idx, t.id] >= x[d.demand_id, s_idx, t.id],
                        name=f"truck_busy_link_{d.demand_id}_{s_idx}_{t.id}_{day_idx}"
                    )
    for t in trucks:
        for day_idx in range(len(planning_horizon)):
            m.addConstr(y[day_idx, t.id] <= 1, name=f"truck_busy_limit_{t.id}_{day_idx}")


    z = m.addVars(planning_horizon_range, lb=0, name="BalanceDeviation")
    slack = m.addVars(planning_horizon_range, lb=0, name="Slack")
    for day in planning_horizon_range:
       m.addConstr(
           gp.quicksum(Load[day] for t in trucks) - AvgLoad <= z[day],
           name=f"pos_dev_{day}",
       )
       m.addConstr(
           AvgLoad - gp.quicksum(Load[day] for t in trucks) <= z[day],
           name=f"neg_dev_{day}",
       )
    
    m.setObjective(
       w_balance * gp.quicksum(z[d] for d in planning_horizon_range)
       + w_slack * gp.quicksum(slack[d] for d in planning_horizon_range),
       GRB.MINIMIZE,
    )
    m.params.OutputFlag = 0  # display solver output
    m.params.TimeLimit = 3600  # 30 minutes
    # Solve
    m.optimize()

    if m.status == GRB.OPTIMAL:
        assignments = []
        for d in demands:
            for s in d.feasible_dates(planning_horizon):
                s_idx = date_to_index[s]
                for k in truck_ids:
                    if x[d.demand_id, s_idx, k].X > 0.5:
                        oa = OrderAssignment(
                            demand=d,
                            assigned_date=index_to_date[s_idx],
                            truck=next(t for t in trucks if t.id == k),
                        )
                        assignments.append(oa)

        daily_loads: Dict = {date: 0.0 for date in planning_horizon}
        for oa in assignments:
            d_obj: Demand = oa.demand
            start_idx = date_to_index[oa.assigned_date]
            for day_offset in range(d_obj.travel_days):
                idx = start_idx + day_offset
                if idx < H:
                    day_date = index_to_date[idx]
                    daily_loads[day_date] += d_obj.weight

        # total capacity per calendar day (test expects sum of truck capacities)
        total_capacity_per_day = sum(t.capacity for t in trucks)
        daily_slack = {
            date: max(0.0, total_capacity_per_day - load)
            for date, load in daily_loads.items()
        }

        # daily balance = abs(Load - AvgLoad) -- compute from daily_loads
        daily_balance = {
            date: abs(load - AvgLoad) for date, load in daily_loads.items()
        }

        # Objective value
        objective_value = m.objVal

        return AssignmentOutput(
            assignments=assignments,
            daily_loads=daily_loads,
            daily_slack=daily_slack,
            daily_balance=daily_balance,
            objective_value=objective_value,
            is_success=True,
        )
    else:
        print(f"No feasible assignment found. status={m.status}")
        return AssignmentOutput(
            assignments=[],
            daily_loads={},
            daily_slack={},
            daily_balance={},
            objective_value=0.0,
            is_success=False,
        )


