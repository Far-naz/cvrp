from src.data_model.assignment_Input import AssignmentInput
from src.business_model.mip.assignment_model.assignement_demands import assign_orders
from src.business_model.mip.capacited_vrp_model.capacited_vrp_model import solve_cvrp   
from src.data_model.assignment_output import AssignmentOutput
from src.data_model.cvrp_input import CVRPInput
from src.data_model.cvrp_output import CVRPOutput, TruckRoute
from src.serializer.serialize_cvrp_input import create_cvrp_input_from_assignment_output


def run_assignment_orders(assignment_input: AssignmentInput) -> AssignmentInput:
    assignment_output = assign_orders(assignment_input)
    return assignment_output

def run_cvrp(assignment_output: AssignmentOutput, assignment_input: AssignmentInput) -> CVRPOutput:
    solutions = {}
    for assigned_date in assignment_output.assignments.keys():
        cvrp_input = create_cvrp_input_from_assignment_output(assignment_input, assignment_output, assigned_date)
        cvrp_output = solve_cvrp(cvrp_input)
        if cvrp_output is None:
            print(f"CVRP could not find a solution for date {assigned_date}")
        else:
            solutions[assigned_date] = cvrp_output
    return solutions