import gurobipy as gp
from gurobipy import GRB
from src.data_model.assignment_demand import OrderAssignment
from src.data_model.assignment_Input import AssignmentInput
from src.data_model.assignment_output import AssignmentOutput
from src.data_model.demand import Demand
from src.data_model.truck import Truck
from datetime import date, datetime
from typing import List, Dict
from collections import defaultdict



def assign_item_to_truck_day(item, truck_id, day, assignments):
    assignments[day][truck_id].append(item)
    item.assigned = True


def assignment_orders_to_trucks_days(input_data: AssignmentInput) -> AssignmentOutput:
    demands: list[Demand] = input_data.demands
    trucks: list[Truck] = input_data.trucks
    planning_horizon: list[date] = input_data.planning_horizon
    
    truck_map = {t.id: t for t in trucks}
    truck_ids = [t.id for t in trucks]


    dest_to_demands = defaultdict(list)
    for d in demands:
        dest_to_demands[d.destination].append(d)

    assignments = {day: {t.id: [] for t in trucks} for day in planning_horizon}

    remaining_items = list(demands)
    for day_idx, day in enumerate(planning_horizon):
        feasible_items = [m for m in remaining_items if day in m.feasible_dates(planning_horizon)]


        total_weight = sum(m.weight for m in feasible_items)
        AvgLoad = total_weight / len(truck_ids) if truck_ids else 0
        
        if not feasible_items:
            continue
        
        # Build mini-MIP for this day
        mini = gp.Model(f"Day_{day_idx}")
        
        x = mini.addVars([m.demand_id for m in feasible_items], truck_ids, vtype=GRB.BINARY)
        u = mini.addVars([m.destination.id for m in feasible_items], lb=0, ub=len(truck_ids), vtype=GRB.INTEGER)
       
        for t_id in truck_ids:
            mini.addConstr(gp.quicksum(x[m.demand_id, t_id] * m.weight for m in feasible_items) <= truck_map[t_id].capacity)
            mini.addConstr(gp.quicksum(x[m.demand_id, t_id] * m.size_area for m in feasible_items) <= truck_map[t_id].inner_size)
            
            for m in feasible_items:
                mini.addConstr(u[m.destination.id] >= x[m.demand_id, t_id])
            mini.addConstr(gp.quicksum(u[m.destination.id] for m in feasible_items) <= 5)
        
        
        T_dev = mini.addVars(truck_ids, lb=0, name="dev")

        for t_id in truck_ids:
            total_load = gp.quicksum(x[m.demand_id, t_id] * m.weight for m in feasible_items)
            mini.addConstr(total_load - AvgLoad <= T_dev[t_id])
            mini.addConstr(AvgLoad - total_load <= T_dev[t_id])

        mini.setObjective(gp.quicksum(T_dev[t_id] for t_id in truck_ids), GRB.MINIMIZE)
        
        mini.optimize()
        
        for m in feasible_items:
            for t_id in truck_ids:
                if x[m.demand_id, t_id].X > 0.5:
                    assign_item_to_truck_day(m, t_id, day, assignments)
                    remaining_items.remove(m)

    daily_loads = {}
    daily_slack = {}
    daily_balance = {}
    for day in planning_horizon:
        total_load = sum(
            sum(m.weight for m in assignments[day][t_id]) for t_id in truck_ids
        )
        daily_loads[day.isoformat()] = total_load
        avg_load = total_load / len(truck_ids) if truck_ids else 0
        daily_balance[day.isoformat()] = avg_load
        daily_slack[day.isoformat()] = max(
            0,
            max(
                sum(m.weight for m in assignments[day][t_id]) for t_id in truck_ids
            ) - avg_load,
        )

    objective_value = sum(daily_slack.values())
    return AssignmentOutput(
        assignments=[
            OrderAssignment(
                demand=item,
                truck=truck_map[truck_id],
                assigned_date=day,
            )
            for day in planning_horizon
            for truck_id in truck_ids
            for item in assignments[day][truck_id]
        ],
        daily_loads=daily_loads,
        daily_slack=daily_slack,
        daily_balance=daily_balance,
        objective_value=objective_value,
        is_success=True,
    )
