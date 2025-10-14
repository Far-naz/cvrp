from src.data_model.cvrp_input import CVRPInput
from src.data_model.assignment_Input import AssignmentInput
from src.data_model.assignment_output import AssignmentOutput
from datetime import date
from collections import defaultdict
from src.data_model.cvrp_input import CVRPInput
from src.data_model.assignment_Input import AssignmentInput
from src.data_model.assignment_output import AssignmentOutput
from src.data_model.demand import Demand

def create_cvrp_input_from_assignment_output(
    assignment_input: AssignmentInput,
    assignment_output: AssignmentOutput,
    assigned_date: date,
    truck_used=None,
    distances=None,
) -> CVRPInput:
    """
    Build CVRPInput from assignment results for a specific date.
    Consolidates all demands for the same factory into a single aggregated demand.
    """
    assigned_demands = [
        a.demand
        for a in assignment_output.assignments
        if a.assigned_date == assigned_date
    ]

    if not assigned_demands:
        raise ValueError(f"No demands found for assigned date {assigned_date}.")

    grouped = defaultdict(list)
    for d in assigned_demands:
        grouped[d.destination.id].append(d)

    consolidated_demands = []

    for factory_id, group in grouped.items():
        first_demand = group[0]
        destination_factory = first_demand.destination

        total_weight = sum(d.weight for d in group)
        total_area = sum(d.size_area for d in group)
        earliest_available = min(d.available_time for d in group)
        latest_due = max(d.due_time for d in group)
        max_travel_days = max(d.travel_days for d in group)

        new_demand_id = f"agg_{factory_id}_{assigned_date.isoformat()}"
        
        new_demand = Demand(
            demand_id=new_demand_id,
            weight=total_weight,
            size_area=total_area,
            destination=destination_factory,
            available_time=earliest_available,
            due_time=latest_due,
            travel_days=max_travel_days,
        )
        consolidated_demands.append(new_demand)

    trucks = truck_used

    cvrp_input = CVRPInput(
        demands=consolidated_demands,
        trucks=trucks,
        distance_matrix=distances,
    )

    return cvrp_input


def create_cvrp_input_from_assignment_output2(
    assignment_input: AssignmentInput,
    assignment_output: AssignmentOutput,
    assigned_date: date,
    distances=None,
) -> CVRPInput:
    ''' extract demands that are assigned on the given date'''
    demands = [
        a.demand
        for a in assignment_output.assignments
        if a.assigned_date == assigned_date
    ]
    trucks = assignment_input.trucks

  
    distance_matrix = distances

    cvrp_input = CVRPInput(
        demands=demands, trucks=trucks, distance_matrix=distance_matrix
    )
    return cvrp_input
