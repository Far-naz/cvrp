import gurobipy as gp
from gurobipy import GRB


# ---------------------------
# Sample data
# ---------------------------
orders = [1, 2, 3, 4, 5]
dates = list(range(1, 4))  # days 1 to 7
q = {1: 5, 2: 4, 3: 3, 4: 6, 5: 2}  # order quantities
pickup = {1: 1, 2: 2, 3: 1, 4: 3, 5: 2}  # earliest pickup date per order
due =    {1: 4, 2: 6, 3: 5, 4: 7, 5: 3}  # latest delivery date per order
Cap = {d: 10 for d in dates}              # truck capacity per day
w_bal = 1
w_slack = 1000

AvgLoad = sum(q[o] for o in orders) / len(dates)

# ---------------------------
# Model
# ---------------------------
m = gp.Model("Order_Assignment_with_DueDates")

# Decision variables
x = m.addVars(orders, dates, vtype=GRB.BINARY, name="x")
Load = m.addVars(dates, lb=0, name="Load")
z = m.addVars(dates, lb=0, name="z")
slack = m.addVars(dates, lb=0, name="slack")

# Each order exactly once
m.addConstrs((gp.quicksum(x[o,d] for d in dates) == 1 for o in orders), name="assign_once")

# Pickup/due date feasibility
for o in orders:
    for d in dates:
        if d < pickup[o] or d > due[o]:
            x[o,d].ub = 0  # force x=0 for infeasible days

# Define daily loads
m.addConstrs((Load[d] == gp.quicksum(q[o]*x[o,d] for o in orders) for d in dates), name="load_def")

# Capacity (with slack)
m.addConstrs((Load[d] <= Cap[d] + slack[d] for d in dates), name="capacity")

# Balance deviation
m.addConstrs((z[d] >= Load[d] - AvgLoad for d in dates), name="pos_dev")
m.addConstrs((z[d] >= AvgLoad - Load[d] for d in dates), name="neg_dev")

# Objective
m.setObjective(w_bal * gp.quicksum(z[d] for d in dates) +
               w_slack * gp.quicksum(slack[d] for d in dates),
               GRB.MINIMIZE)

# ---------------------------
# Solve
# ---------------------------
m.optimize()

# ---------------------------
# Results
# ---------------------------
if m.status == GRB.OPTIMAL:
    print(f"\nOptimal Objective: {m.objVal:.2f}\n")
    for o in orders:
        for d in dates:
            if x[o,d].x > 0.5:
                print(f"Order {o} -> Day {d}")
    for d in dates:
        print(f"Day {d}: Load={Load[d].x:.1f}, Slack={slack[d].x:.1f}, z={z[d].x:.1f}")
