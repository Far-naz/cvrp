import gurobipy as gp
from gurobipy import GRB
from src.data_model.cvrp_input import CVRPInput
from src.data_model.cvrp_output import CVRPOutput, TruckRoute
from src.data_model.factory import Factory, create_depot_factory
from src.data_model.truck import Truck
import config
from datetime import datetime


def solve_cvrp_gg(input_data: CVRPInput) -> CVRPOutput:
    demands = input_data.demands
    trucks = input_data.trucks
    C = input_data.distance_matrix

    depot_factory = create_depot_factory()
    factories = [depot_factory] + [d.destination for d in demands]

    factory_to_index = {f.id: f for f in factories}

    nodes = [config.DEPOT_ID] + [d.destination.id for d in demands]
    N = len(nodes)

    q = {d.destination.id: d.weight for d in demands}
    q[config.DEPOT_ID] = 0.0  # depot load is total demand

    available_trucks: list[Truck] = trucks

    num_vehicles = len(available_trucks)
    Q = [t.capacity for t in available_trucks]

    print(
        f"total number of demands: {N}, nodes are {nodes}, number of vehicles: {num_vehicles}"
    )

    ready = {i: 0.0 for i in range(N)}
    due = {i: float("inf") for i in range(N)}
    service_time = config.SERVICE_TIME_PER_STOP
    for idx, d in enumerate(demands, start=1):
        ready[d.destination.id] = d.available_minutes
        due[d.destination.id] = d.due_minutes

    max_c = max(C[i][j] for i in C for j in C[i])
    C_norm = {i: {j: C[i][j] / max_c for j in C[i]} for i in C}

    m = gp.Model("CVRP")

    x = m.addVars(nodes, nodes, range(num_vehicles), vtype=GRB.BINARY, name="x")
    f = m.addVars(nodes, nodes, range(num_vehicles), lb=0, name="f")
    visit = m.addVars(nodes, range(num_vehicles), vtype=GRB.BINARY, name="visit")

    m.setObjective(
        gp.quicksum(
            available_trucks[k].cost * C_norm[i][j] * x[i, j, k]
            for k in range(num_vehicles)
            for i in nodes
            for j in nodes
            if i != j
        )
        + config.SERVICE_COST_PER_STOP
        * gp.quicksum(
            visit[j, k]
            for k in range(num_vehicles)
            for j in nodes
            if j != config.DEPOT_ID
        )
        + gp.quicksum(
            f[i, j, k] * 0.01
            for k in range(num_vehicles)
            for i in nodes
            for j in nodes
            if i != j
        ),
        GRB.MINIMIZE,
    )

    m.addConstr(
        gp.quicksum(
            x[config.DEPOT_ID, j, k] for j in nodes[1:] for k in range(num_vehicles)
        )
        == num_vehicles
    )
    m.addConstrs(
        gp.quicksum(visit[i, k] for k in range(num_vehicles)) == 1
        for i in nodes
        if i != config.DEPOT_ID
    )

    for k in range(num_vehicles):
        for h in nodes:
            m.addConstr(
                gp.quicksum(x[i, h, k] for i in nodes if i != h)
                == gp.quicksum(x[h, j, k] for j in nodes if j != h),
                name=f"flow_conservation_{h}_{k}",
            )

    for k in range(num_vehicles):
        for i in nodes:
            m.addConstr(
                gp.quicksum(x[i, j, k] for j in nodes if i != j) == visit[i, k],
                name=f"visit_link_{i}_{k}",
            )

    for k in range(num_vehicles):
        m.addConstr(
            gp.quicksum(visit[j, k] for j in nodes if j != config.DEPOT_ID)
            <= config.MAX_STOPS
        )

    for i in nodes[1:]:
        for k in range(num_vehicles):
            m.addConstr(
                gp.quicksum(f[j, i, k] for j in nodes if j != i)
                - gp.quicksum(f[i, j, k] for j in nodes if j != i)
                == q[i] * visit[i, k],
                name=f"flow_conservation_load_{i}_{k}",
            )
    for i in nodes:
        for j in nodes[1:]:
            if i != j:
                for k in range(num_vehicles):
                    m.addConstr(
                        f[i, j, k] >= q[i]*x[i, j, k],
                        name=f"flow_cap_{i}_{j}_{k}",
                    )
    for k in range(num_vehicles):
        for i in nodes:
            for j in nodes[1:]:
                if i != j:
                    m.addConstr(
                        f[i, j, k] <= (Q[k] - q[i]) * x[i, j, k],
                        name=f"load_cap2_{j}_{k}",
                    )
    for k in range(num_vehicles):
        for j in nodes[1:]:
            m.addConstr(
                f[config.DEPOT_ID, j, k] <= Q[k] * x[config.DEPOT_ID, j, k],
                name=f"load_cap_{j}_{k}",
            )
    m.params.OutputFlag = 0  # turn off output
    m.params.TimeLimit = 600  # 10 minutes
    m.optimize()

    if m.status == GRB.OPTIMAL:
        print(f"Optimal objective: {m.objVal}")
        # visited nodes
        for k in range(num_vehicles):
            for i in nodes:
                for j in nodes:
                    if x[i, j, k].X > 0.5:
                        print(f"Truck {k} travels from {i} to {j}")

        routes_output = []
        cvrp_travel_cost: int = 0
        cvrp_handling_cost: int = 0
        cvrp_total_distance: float = 0.0
        for k, t in enumerate(available_trucks):
            route_indices = [config.DEPOT_ID]  # start at depot
            load_seq = [0.0]
            start_time = [0.0]
            travel_times = [0.0]
            start_time_dt = []
            current_node = config.DEPOT_ID
            visited = set()
            while True:
                next_nodes = [
                    j
                    for j in nodes
                    if j != current_node
                    and x[current_node, j, k].X > 0.5
                    and j not in visited
                ]
                if not next_nodes:
                    break
                next_node = next_nodes[0]
                route_indices.append(next_node)
                load_seq.append(
                    f[current_node, next_node, k].X
                    if next_node != config.DEPOT_ID
                    else 0.0
                )
                travel_time = (C[current_node][next_node] / t.speed) * 60
                if current_node == config.DEPOT_ID and len(route_indices) == 2:
                    st = 0.0
                else:
                    if next_node == config.DEPOT_ID:
                        st = start_time[-1] + service_time + travel_time
                    else:
                        st = start_time[-1] + service_time + travel_time

                start_time.append(st)
                dt = datetime.fromtimestamp(st * 60)
                start_time_dt.append(str(dt.strftime("%H:%M")))
                travel_times.append(travel_time)
                visited.add(next_node)
                current_node = next_node

            if len(route_indices) > 1:
                route_factories = [factory_to_index[i] for i in route_indices]
                # total_cost = m.objVal

                travel_cost = 0.0
                handling_cost = 0.0
                total_travel_distance = 0.0
                total_travel_time = 0.0
                for i, r_id in enumerate(route_indices[:-1]):
                    i_id = r_id
                    j_id = route_indices[i + 1]
                    travel_cost += available_trucks[k].cost * (C[i_id][j_id])
                    total_travel_distance += C[i_id][j_id]
                    total_travel_time += C[i_id][j_id] / available_trucks[k].speed
                    if j_id != config.DEPOT_ID:
                        handling_cost += config.SERVICE_COST_PER_STOP
                cvrp_total_distance += total_travel_distance

                total_stops = len(route_indices)-2
                routes_output.append(
                    TruckRoute(
                        truck=t,
                        route=route_factories,
                        unload_at_node=load_seq,
                        times_at_node=start_time_dt,
                        travel_times_at_node=travel_times,
                        travel_distance=total_travel_distance,
                        travel_time=total_travel_time,
                        total_stops=total_stops,
                        total_travel_cost=travel_cost,
                        total_handling_cost=handling_cost,
                    )
                )

                cvrp_travel_cost += travel_cost
                cvrp_handling_cost += handling_cost

        return CVRPOutput(
            routes=routes_output,
            total_cost=cvrp_travel_cost + cvrp_handling_cost,
            travel_cost=cvrp_travel_cost,
            handling_cost=cvrp_handling_cost,
            total_travel_distance=cvrp_total_distance,
            is_success=True,
        )
    else:
        print(f"No optimal solution found for CVRP ")
        return CVRPOutput(routes=[], total_cost=0.0, is_success=False)



def solve_cvrp_tw(input_data: CVRPInput) -> CVRPOutput:
    demands = input_data.demands
    trucks = input_data.trucks
    C = input_data.distance_matrix
    depot_factory = create_depot_factory()

    customers = [d.destination for d in demands]
    nodes = [depot_factory] + customers
    N = len(nodes)
    num_vehicles = len(trucks)

    q = {i: 0 for i in range(N)}
    ready = {i: 0.0 for i in range(N)}
    due = {i: float("inf") for i in range(N)}
    service_time = config.SERVICE_TIME_PER_STOP
    for idx, d in enumerate(demands, start=1):
        q[idx] = d.weight
        ready[idx] = getattr(
            d.destination,
            "available_time",
            getattr(d.destination, "available_clock", 0.0),
        )
        due[idx] = getattr(
            d.destination, "due_time", getattr(d.destination, "due_clock", float("inf"))
        )

    ready[0] = 0.0
    due[0] = max(due.values()) + 1000.0

    Q = [t.capacity for t in trucks]
    costs = [t.cost for t in trucks]

    m = gp.Model("CVRP_TW")

    # decision arcs
    x = m.addVars(N, N, num_vehicles, vtype=GRB.BINARY, name="x")
    load = m.addVars(range(1, N), range(num_vehicles), lb=0.0, ub=max(Q), name="load")
    arrival = m.addVars(range(N), range(num_vehicles), lb=0.0, name="arrival")
    visit = m.addVars(range(1, N), range(num_vehicles), vtype=GRB.BINARY, name="visit")

    m.setObjective(
        gp.quicksum(
            costs[k] * C[i][j] * x[i, j, k]
            for k in range(num_vehicles)
            for i in range(N)
            for j in range(N)
            if i != j
        )
        + config.SERVICE_COST_PER_STOP
        * gp.quicksum(visit[j, k] for k in range(num_vehicles) for j in range(1, N)),
        GRB.MINIMIZE,
    )

    # --- Constraints ---

    # 1) Each customer visited exactly once across all vehicles
    for j in range(1, N):
        m.addConstr(
            gp.quicksum(
                x[i, j, k] for k in range(num_vehicles) for i in range(N) if i != j
            )
            == 1,
            name=f"visit_once_{j}",
        )

    # 2) Flow conservation per vehicle: if vehicle visits a customer, incoming == outgoing
    for k in range(num_vehicles):
        for j in range(1, N):
            m.addConstr(
                gp.quicksum(x[i, j, k] for i in range(N) if i != j)
                == gp.quicksum(x[j, l, k] for l in range(N) if l != j),
                name=f"flow_cons_{j}_{k}",
            )

    # 3) Depot departure/return: each vehicle can depart at most once (<=1 to allow unused vehicles)
    for k in range(num_vehicles):
        m.addConstr(
            gp.quicksum(x[0, j, k] for j in range(1, N)) <= 1, name=f"depart_once_{k}"
        )
        m.addConstr(
            gp.quicksum(x[i, 0, k] for i in range(1, N)) <= 1, name=f"return_once_{k}"
        )
        # link departures and returns (if it departs then must return)
        m.addConstr(
            gp.quicksum(x[0, j, k] for j in range(1, N))
            == gp.quicksum(x[i, 0, k] for i in range(1, N)),
            name=f"depart_return_eq_{k}",
        )

    # 4) Link visit var to incoming arcs
    for k in range(num_vehicles):
        for j in range(1, N):
            m.addConstr(
                gp.quicksum(x[i, j, k] for i in range(N) if i != j) == visit[j, k],
                name=f"visit_link_{j}_{k}",
            )

    # 5) Capacity propagation (load variables)
    # load[j,k] >= load[i,k] + q[j] - Q[k] * (1 - x[i,j,k]) for i != j, i can be depot(0) but load at depot is 0
    for k in range(num_vehicles):
        for i in range(N):
            for j in range(1, N):
                if i == j:
                    continue
                if i == 0:
                    m.addConstr(
                        load[j, k] >= q[j] - Q[k] * (1 - x[0, j, k]),
                        name=f"cap_from_depot_{i}_{j}_{k}",
                    )
                else:
                    m.addConstr(
                        load[j, k] >= load[i, k] + q[j] - Q[k] * (1 - x[i, j, k]),
                        name=f"cap_prop_{i}_{j}_{k}",
                    )
    # bounds: if not visited, load can be zero via big-M; enforce upper bound tight
    for k in range(num_vehicles):
        for j in range(1, N):
            m.addConstr(load[j, k] <= Q[k] * visit[j, k], name=f"load_ub_{j}_{k}")
            m.addConstr(load[j, k] >= q[j] * visit[j, k], name=f"load_lb_{j}_{k}")

    # 6) Total load per vehicle not exceeding capacity implicitly enforced by propagation and lbs/ubs
    # also explicit (optional):
    for k in range(num_vehicles):
        m.addConstr(
            gp.quicksum(q[j] * visit[j, k] for j in range(1, N)) <= Q[k],
            name=f"cap_total_{k}",
        )

    # 7) Time windows and travel time propagation
    # Compute a safe big_M
    max_travel = max(C[i][j] for i in range(N) for j in range(N) if i != j)
    earliest = min(ready.values())
    latest = max(due.values())
    big_M = (latest - earliest) + max_travel + service_time + 100.0

    for k in range(num_vehicles):
        for i in range(N):
            for j in range(N):
                if i == j:
                    continue
                m.addConstr(
                    arrival[j, k]
                    >= arrival[i, k]
                    + service_time
                    + C[i][j]
                    - big_M * (1 - x[i, j, k]),
                    name=f"time_prop_{i}_{j}_{k}",
                )

        # time window enforcement for customers if visited
        for j in range(1, N):
            m.addConstr(
                arrival[j, k] >= ready[j] - big_M * (1 - visit[j, k]),
                name=f"ready_{j}_{k}",
            )
            m.addConstr(
                arrival[j, k] <= due[j] + big_M * (1 - visit[j, k]), name=f"due_{j}_{k}"
            )

    # Optional: bound arrival at depot if you want to compute return times: no special constraint except derivation
    # limit maximum arrival time
    # for k in range(num_vehicles):
    #    m.addConstr(arrival[0, k] >= 0.0, name=f"depot_time_lb_{k}")

    # 8) Max stops per vehicle
    for k in range(num_vehicles):
        m.addConstr(
            gp.quicksum(visit[j, k] for j in range(1, N)) <= config.MAX_STOPS,
            name=f"max_stops_{k}",
        )

    # Solve
    m.params.OutputFlag = 0
    m.params.TimeLimit = 600
    m.optimize()

    routes_output = []
    total_cost = None
    if m.status in (GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL):
        total_cost = m.objVal
        # extract routes: follow arcs from depot for each vehicle
        for k in range(num_vehicles):
            # find departure from depot
            dep_next = [j for j in range(1, N) if x[0, j, k].X > 0.5]
            if not dep_next:
                continue  # vehicle unused
            route_nodes = [0]
            loads = [0.0]  # load after visiting depot (0)
            arrivals = [float(arrival[0, k].X)]
            cur = dep_next[0]
            visited = set([0])
            # follow path until returns to depot
            while True:
                route_nodes.append(cur)
                if cur == 0:
                    break
                # load after visiting cur
                loads.append(load[cur, k].X if cur != 0 else 0.0)
                arrivals.append(arrival[cur, k].X)
                visited.add(cur)
                # find next
                next_candidates = [
                    j for j in range(N) if j != cur and x[cur, j, k].X > 0.5
                ]
                if not next_candidates:
                    # if no explicit next, try to find return-to-depot
                    if x[cur, 0, k].X > 0.5:
                        route_nodes.append(0)
                        arrivals.append(arrival[0, k].X)
                        loads.append(0.0)
                    break
                cur = next_candidates[0]
                if cur == 0:
                    route_nodes.append(0)
                    arrivals.append(arrival[0, k].X)
                    loads.append(0.0)
                    break
                if cur in visited:
                    # precaution to avoid infinite loops
                    break

            # map route node indices back to factory objects
            route_factories = [nodes[i] for i in route_nodes]
            routes_output.append(
                TruckRoute(
                    truck=trucks[k], route=route_factories, unload_at_node=arrivals
                )
            )

        return CVRPOutput(routes=routes_output, total_cost=total_cost, is_success=True)
    else:
        # infeasible or no solution
        return CVRPOutput(routes=[], total_cost=0.0, is_success=False)
