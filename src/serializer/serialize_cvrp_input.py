from src.data_model.cvrp_input import CVRPInput
from src.data_model.assignment_Input import AssignmentInput
from src.data_model.assignment_output import AssignmentOutput
from datetime import date
from src.data_model.factory import Factory, create_depot_factory
from src.data_model.distance import build_distance_matrix

def create_cvrp_input_from_assignment_output(assignment_input:AssignmentInput, assignment_output: AssignmentOutput, assigned_date: date) -> CVRPInput:
    demands = assignment_output.assignments.get(assigned_date, [])
    trucks = assignment_input.trucks

    destinations = [d.destination for d in demands]
    depot = create_depot_factory()
    all_locations = [depot] + destinations

    distance_matrix = build_distance_matrix(all_locations)
    
    cvrp_input = CVRPInput(
        demands=demands,
        trucks=trucks,
        distance_matrix=distance_matrix
    )
    return cvrp_input