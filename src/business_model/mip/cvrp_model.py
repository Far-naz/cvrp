import gurobipy as gp
from gurobipy import GRB


def create_cvrp_model(distance_matrix, vehicle_capacity, orders, depot_index=0):
    num_orders = len(orders)
    num_vehicles = num_orders  # Upper bound on number of vehicles

    model = gp.Model("CVRP")

    # Decision variables
    x = model.addVars(num_orders + 1, num_orders + 1, num_vehicles, vtype=GRB.BINARY, name="x")
    u = model.addVars(num_orders + 1, vtype=GRB.CONTINUOUS, name="u")

    # Objective: Minimize total distance traveled
    model.setObjective(gp.quicksum(distance_matrix[i][j] * x[i, j, k]
                                    for i in range(num_orders + 1)
                                    for j in range(num_orders + 1)
                                    for k in range(num_vehicles) if i != j), GRB.MINIMIZE)

    # Constraints
    # Each order is visited exactly once
    for j in range(1, num_orders + 1):
        model.addConstr(gp.quicksum(x[i, j, k] for i in range(num_orders + 1) for k in range(num_vehicles) if i != j) == 1, name=f"visit_{j}")

    # Flow conservation constraints
    for k in range(num_vehicles):
        model.addConstr(gp.quicksum(x[depot_index, j, k] for j in range(1, num_orders + 1)) <= 1, name=f"depart_{k}")
        model.addConstr(gp.quicksum(x[i, depot_index, k] for i in range(1, num_orders + 1)) <= 1, name=f"return_{k}")

        for h in range(1, num_orders + 1):
            model.addConstr(gp.quicksum(x[i, h, k] for i in range(num_orders + 1) if i != h) ==
                            gp.quicksum(x[h, j, k] for j in range(num_orders + 1) if j != h), name=f"flow_{h}_{k}")

    # total number of stops for each vehicle is less than or equal to 5
    for k in range(num_vehicles):
        model.addConstr(gp.quicksum(x[i, j, k] for i in range(num_orders + 1)
                                    for j in range(1, num_orders + 1) if i != j) <= 5, name=f"max_stops_{k}")

    # Subtour elimination and capacity constraints
    for k in range(num_vehicles):
        for i in range(1, num_orders + 1):
            model.addConstr(u[i] >= orders[i - 1].weight, name=f"load_min_{i}_{k}")
            model.addConstr(u[i] <= vehicle_capacity, name=f"load_max_{i}_{k}")
            for j in range(1, num_orders + 1):
                if i != j:
                    model.addConstr(u[i] - u[j] + vehicle_capacity * x[i, j, k] <= vehicle_capacity - orders[j - 1].weight, name=f"subtour_{i}_{j}_{k}")
    model.update()
    return model

def get_solution(model, orders):
    if model.status == GRB.OPTIMAL:
        solution = []
        num_orders = len(orders)
        num_vehicles = num_orders
        x = model.getVars()
        for k in range(num_vehicles):
            route = []
            for i in range(num_orders + 1):
                for j in range(num_orders + 1):
                    if i != j and model.getVarByName(f"x[{i},{j},{k}]").X > 0.5:
                        route.append((i, j))
            if route:
                solution.append(route)
        return solution
    else:
        return None
    
    