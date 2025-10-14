from src.data_model.assignment_Input import AssignmentInput
from src.serializer.serialize_order import get_demands_from_order_data_frame
from src.serializer.serializer_truck import create_truck_from_data_frame
from datetime import timedelta

def get_assignment_input_schema()-> AssignmentInput:
    demands = get_demands_from_order_data_frame()
    trucks = create_truck_from_data_frame()

    earliest_date = min(d.available_time.date() for d in demands)
    latest_date = max(d.due_time.date() for d in demands)
    planning_horizon = [earliest_date + timedelta(days=i) for i in range((latest_date - earliest_date).days + 1)]

    input_data = AssignmentInput(
        demands=demands,
        trucks=trucks,
        planning_horizon=planning_horizon,
        w_balance=1.0,
        w_slack=1000.0
    )
    return input_data