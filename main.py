import json

import config
from src.business_model.mip.assignment_model.order_assignment import (
    assignment_orders_to_trucks_days,
)
from src.business_model.mip.capacited_vrp_model.capacited_vrp_model import solve_cvrp_gg
from src.serializer.serialize_order import (
    create_factory_from_order_data,
    get_factory_list_from_order_data_frame,
    get_demands_from_order_data_frame,
)

from src.serializer.serialize_cvrp_input import create_cvrp_input_from_assignment_output
from src.serializer.serializer_truck import create_truck_from_data_frame
from src.serializer.serialize_distance import serialize_distance_from_data_frame
from src.data_model.assignment_Input import AssignmentInput
from src.data_model.assignment_output import AssignmentOutput
from src.data_model.factory import Factory
from src.data_model.demand import Demand
from src.data_model.truck import Truck
from src.data_model.cvrp_input import CVRPInput
from src.data_model.cvrp_output import CVRPOutput
from src.data_model.order import Order
from typing import Dict
import pandas as pd

order_data = config.ORDER_LARGE_CSV
time_format = (
    config.ORDER_LARGE_DATE
    if order_data == config.ORDER_LARGE_CSV
    else config.ORDER_SMALL_DATE
)

run_first: bool = False


def read_and_serialize_order() -> list[Order]:
    return pd.read_csv(order_data, encoding="cp1252")


def read_and_serialize_demand(distances: dict[tuple[int, int], float]) -> list[Demand]:
    order_df = pd.read_csv(order_data, encoding="cp1252")
    demands = get_demands_from_order_data_frame(order_df, distances, time_format)
    return demands


def read_and_serialize_truck() -> list[Truck]:
    truck_df = pd.read_csv(config.TRUCK_CSV)
    trucks: Dict[str, Truck] = create_truck_from_data_frame(truck_df)
    return list(trucks.values())


def read_and_serialize_factory() -> dict[str, Factory]:
    order_df = pd.read_csv(order_data, encoding="cp1252")
    factories: Dict[str, Factory] = get_factory_list_from_order_data_frame(order_df)
    return factories


def read_and_serialize_distance(
    factories: dict[int, Factory],
) -> dict[tuple[int, int], float]:
    distance_df = pd.read_csv(config.DISTANCE_CSV)
    distances = serialize_distance_from_data_frame(distance_df, factories)
    return distances


def prepare_model_input(demands, trucks, distances) -> AssignmentInput:
    planning_horizon = sorted(
        {
            order.available_date + pd.Timedelta(days=i)
            for order in demands
            for i in range((order.due_date - order.available_date).days + 1)
        }
    )
    return AssignmentInput(
        demands=demands,
        trucks=trucks,
        distances=distances,
        planning_horizon=planning_horizon,
        w_balance=1.0,
        w_slack=10.0,
    )


def run_assignment():
    orders = read_and_serialize_order()
    factories = create_factory_from_order_data(orders)
    distances = read_and_serialize_distance(factories)

    demands = read_and_serialize_demand(distances)
    trucks = read_and_serialize_truck()

    print(f"Total demands: {len(demands)}")
    print(f"Total trucks: {len(trucks)}")

    model_input: AssignmentInput = prepare_model_input(demands, trucks, distances)
    if run_first:

        result_assignment: AssignmentOutput = assignment_orders_to_trucks_days(
            model_input
        )
        if result_assignment.is_success:
            with open("assignment_result_1.json", "w") as f:
                f.write(result_assignment.model_dump_json(indent=2))
        if not result_assignment.is_success:
            print("No feasible assignment found.")
            return None

    else:
        # read from a file1
        with open("assignment_result_1.json", "r") as f:
            result_assignment = AssignmentOutput.model_validate(json.load(f))

    if result_assignment.is_success:


        assigned_dates = sorted(
            {assgn.assigned_date for assgn in result_assignment.assignments}
        )
        cvrp_result = {}
        for assigned_date in assigned_dates[0:1]:
            # extract trucks used that day
            truck_used = {
                assgn.truck
                for assgn in result_assignment.assignments
                if assgn.assigned_date == assigned_date
            }
            truck_used = list(truck_used)
            print(f"Assigned date: {assigned_date}, trucks used: {truck_used}")
            cvrp_input: CVRPInput = create_cvrp_input_from_assignment_output(
                model_input,
                result_assignment,
                assigned_date=assigned_date,
                truck_used=truck_used,
                distances=distances,
            )

            result_cvrp: CVRPOutput = solve_cvrp_gg(cvrp_input)
            if result_cvrp.is_success:
                cvrp_result[assigned_date] = result_cvrp

    with open("cvrp_result_2.json", "w") as f:
        json.dump(
            {
                date.isoformat(): result.model_dump()
                for date, result in cvrp_result.items()
            },
            f,
            indent=2,
            default=str,
        )

    return result_assignment, cvrp_result


def main():
    run_assignment()
    print("solution completed!")
    # save in json or feather


if __name__ == "__main__":
    main()
