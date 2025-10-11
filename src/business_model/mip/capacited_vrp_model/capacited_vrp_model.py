import gurobipy as gp
from gurobipy import GRB
from src.data_model.cvrp_input import CVRPInput
from src.data_model.cvrp_output import CVRPOutput, TruckRoute
from src.data_model.factory import Factory, create_depot_factory


def solve_cvrp(input_data: CVRPInput) -> CVRPOutput:
    demands = input_data.demands
    trucks = input_data.trucks
    C = input_data.distance_matrix

    depot_factory = create_depot_factory()
    factories = [depot_factory] + [d.destination for d in demands]

    index_to_factory = {i: f for i, f in enumerate(factories)}
    factory_to_index = {f.id: i for i, f in enumerate(factories)}

    num_customers = len(demands)
    nodes = [0] + [d.destination.id for d in demands]  # 0 = depot
    num_vehicles = len(trucks)

    Q = [t.capacity for t in trucks]
    q = [0] + [d.weight for d in demands]  # depot has 0 demand

    # Model
    m = gp.Model("CVRP")

    # Decision variables
    x = m.addVars(nodes, nodes, range(num_vehicles), vtype=GRB.BINARY, name="x")
    u = m.addVars(nodes[1:], range(num_vehicles), lb=0, ub=max(Q), name="u")  # cumulative load

    # Objective: minimize total distance
    m.setObjective(
        gp.quicksum(C[i][j] * x[i,j,k] for i in nodes for j in nodes if i != j for k in range(num_vehicles)),
        GRB.MINIMIZE
    )

    # Each customer visited exactly once
    m.addConstrs(
        gp.quicksum(x[i,j,k] for j in nodes if j != i for k in range(num_vehicles)) == 1
        for i in nodes[1:]
    )

    # Flow conservation for vehicles
    m.addConstrs(
        gp.quicksum(x[i,j,k] for j in nodes if j != i) - gp.quicksum(x[j,i,k] for j in nodes if j != i) == 0
        for i in nodes[1:] for k in range(num_vehicles)
    )

    # MTZ subtour elimination / capacity constraints
    m.addConstrs(
        (u[i,k] - u[j,k] + Q[k] * x[i,j,k] <= Q[k] - q[j])
        for i in nodes[1:] for j in nodes[1:] if i != j for k in range(num_vehicles)
    )
    m.addConstrs(
        (q[i] <= u[i,k]) for i in nodes[1:] for k in range(num_vehicles)
    )

    # Depot departure and return
    m.addConstrs(gp.quicksum(x[0,j,k] for j in nodes[1:]) == 1 for k in range(num_vehicles))
    m.addConstrs(gp.quicksum(x[i,0,k] for i in nodes[1:]) == 1 for k in range(num_vehicles))

    # Solve
    m.optimize()

    # Extract solution
    routes_output = []
    for k, t in enumerate(trucks):
        route_indices = [0]  # start at depot
        load_seq = [0.0]
        current_node = 0
        visited = set()
        while True:
            next_nodes = [j for j in nodes if j != current_node and x[current_node,j,k].x > 0.5 and j not in visited]
            if not next_nodes:
                break
            next_node = next_nodes[0]
            route_indices.append(next_node)
            load_seq.append(u[next_node,k].x if next_node != 0 else 0.0)
            visited.add(next_node)
            current_node = next_node
        route_indices.append(0)  # return to depot
        load_seq.append(0.0)

        if len(route_indices) > 2:  # truck used
            route_factories = [index_to_factory[i] for i in route_indices]
            routes_output.append(TruckRoute(truck=t, route=route_factories, unload_at_node=load_seq))

        total_cost = m.objVal
        return CVRPOutput(routes=routes_output, total_cost=total_cost)
    else:
        raise Exception("No optimal solution found for CVRP")
