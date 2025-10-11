import gurobipy as gp
from gurobipy import GRB

# MIP model that assign orders to each date to balance the workload and ensure totalweight < available capacity and order availabe and due date satisfy the assigned date
def create_assignment_model(orders, vehicle_capacity, date_list):
    num_orders = len(orders)
    num_dates = len(date_list)

    model = gp.Model("Order_Assignment")

    # Decision variables
    x = model.addVars(num_orders, num_dates, vtype=GRB.BINARY, name="x")

    # Objective: Minimize the maximum load on any date
    max_load = model.addVar(vtype=GRB.CONTINUOUS, name="max_load")
    model.setObjective(max_load, GRB.MINIMIZE)

    # Constraints
    # Each order is assigned to exactly one date
    for i in range(num_orders):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_dates)) == 1, name=f"assign_{i}")

    # Load on each date should not exceed vehicle capacity and should be less than max_load
    for j in range(num_dates):
        model.addConstr(gp.quicksum(orders[i].weight * x[i, j] for i in range(num_orders)) <= vehicle_capacity, name=f"capacity_{j}")
        model.addConstr(gp.quicksum(orders[i].weight * x[i, j] for i in range(num_orders)) <= max_load, name=f"max_load_{j}")

        # Ensure orders are only assigned to dates within their available and due dates
        for i in range(num_orders):
            if not (orders[i].available_date <= date_list[j] <= orders[i].due_date):
                model.addConstr(x[i, j] == 0, name=f"date_constraint_{i}_{j}")


    model.update()
    return model

def get_assignment_solution(model, orders, date_list):
    if model.status == GRB.OPTIMAL:
        assignment = {date: [] for date in date_list}
        num_orders = len(orders)
        num_dates = len(date_list)
        for i in range(num_orders):
            for j in range(num_dates):
                if model.getVarByName(f"x[{i},{j}]").X > 0.5:
                    assignment[date_list[j]].append(orders[i])
        return assignment
    
    return None

