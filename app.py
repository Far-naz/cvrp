from datetime import date, datetime
import streamlit as st
import json
import pandas as pd

from src.data_model.cvrp_output import CVRPOutput
from src.data_model.cvrp_output import TruckRoute

st.set_page_config(page_title="Assignment Results Viewer", layout="wide")

st.title("🚚 Order Assignment Results")


def display_cvrp_routes(cvrp_output: CVRPOutput, assignments_df: pd.DataFrame):
    st.header("Truck Routes Overview")

    for i, route in enumerate(cvrp_output.routes):
        # truck info
        truck_capacity_weight = (
            route.truck.capacity
            if hasattr(route.truck, "capacity")
            else "N/A"
        )
        truck_capacity_volume = (
            route.truck.inner_size
            if hasattr(route.truck, "inner_size")
            else "N/A"
        )
        
        st.markdown(
            f"### 🚛 Truck Details: Capacity Weight: {truck_capacity_weight} kg | Capacity Volume: {truck_capacity_volume} m² "
        )
        # st.subheader(f"🚚 Truck {route.truck.truck_id if hasattr(route.truck, 'truck_id') else i+1}")

        rows = []
        for j, factory in enumerate(route.route):
            arrival_time = None
            departure_time = None

            demand_info = assignments_df[
                assignments_df["Destination"]
                == getattr(factory, "name", f"Factory {j+1}")
            ]
            if not demand_info.empty:
                demand_weights = demand_info["Weight(kg)"].sum()
                demand_sizes = demand_info["Size"].sum()

            if route.times_at_node and len(route.times_at_node) > j:
                arrival_time = route.times_at_node[j]

            if route.times_at_node and len(route.times_at_node) > j + 1:
                departure_time = route.times_at_node[j + 1]

            rows.append(
                {
                    "Destination": getattr(factory, "name", f"Factory {j+1}"),
                    "Arrival Time": arrival_time,
                    "Departure Time": departure_time,
                    "Total Weight (kg)": demand_weights if not demand_info.empty else 0,
                    "Total Size": demand_sizes if not demand_info.empty else 0,
                }
            )

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)

        st.subheader("📈 Summary")
        col1, col2 = st.columns(2)
        # col1.markdown(f"**Total distance:** {route.travel_distance or 0:.2f} km")
        # col1.markdown(f"**Total time:** {route.travel_time or 0:.2f} h")
        col1.markdown(f"**Total travel cost:** {route.total_travel_cost or 0:.2f}")
        col2.markdown(f"**Total handling cost:** {route.total_handling_cost or 0:.2f}")
        st.markdown("---")


# --- Load JSON file ---
try:
    with open("assignment_result_main.json", "r") as f:
        assignment_data = json.load(f)
except FileNotFoundError:
    st.error(
        "assignment_result.json not found. Please run the assignment function first."
    )
    st.stop()

# --- Show raw JSON (optional) ---
with st.expander("View raw JSON data"):
    st.json(assignment_data)

# --- Extract key info ---
assignments = assignment_data.get("assignments", [])
daily_loads = assignment_data.get("daily_loads", {})
daily_balance = assignment_data.get("daily_balance", {})
daily_slack = assignment_data.get("daily_slack", {})
objective_value = assignment_data.get("objective_value", None)
# is_success = assignment_data.get("is_success", None)

# --- Summary section ---
# st.subheader("📈 Summary")
# col1, col2 = st.columns(2)
# col1.metric("Objective Value", f"{objective_value:.2f}" if objective_value else "N/A")
# col2.metric("Daily Balance", f"{daily_balance:.2f}" if daily_balance else "N/A")
# col2.metric("Success", "✅ Yes" if is_success else "❌ No")

# --- Assignments table ---
if assignments:
    assignments_df = pd.DataFrame(
        [
            {
                "Destination": (
                    a["demand"]["destination"]["name"]
                    if "demand" in a and "destination" in a["demand"]
                    else None
                ),
                "Item_Id": (
                    a["demand"]["demand_id"]
                    if "demand" in a and "demand_id" in a["demand"]
                    else None
                ),
                "Weight(kg)": (
                    a["demand"]["weight"]
                    if "demand" in a and "weight" in a["demand"]
                    else None
                ),
                "Size": (
                    a["demand"]["size_area"]
                    if "demand" in a and "size_area" in a["demand"]
                    else None
                ),
                "Assigned date": a.get("assigned_date"),
                "Available date": (
                    datetime.fromisoformat(a["demand"]["available_time"]).date()
                    if "demand" in a and "available_time" in a["demand"]
                    else None
                ),
                "Due date": (
                    datetime.fromisoformat(a["demand"]["due_time"]).date()
                    if "demand" in a and "due_time" in a["demand"]
                    else None
                ),
            }
            for a in assignments
        ]
    )
    assignments_df["assigned_date_df"] = pd.to_datetime(assignments_df["Assigned date"])
else:
    assignments_df = pd.DataFrame(columns=["demand_id", "truck_id", "assigned_date"])

if daily_loads:
    daily_loads_df = pd.DataFrame(list(daily_loads.items()), columns=["Date", "Load"])
    daily_loads_df["Date"] = pd.to_datetime(daily_loads_df["Date"])
else:
    daily_loads_df = pd.DataFrame(columns=["Date", "Load"])


st.subheader("🗓️ Filter by Assigned Date")
if not assignments_df.empty:
    min_date = assignments_df["assigned_date_df"].min().date()
    max_date = assignments_df["assigned_date_df"].max().date()
    selected_date = st.date_input(
        "Select date to filter assignments:",
        value=min_date,
        min_value=min_date,
        max_value=max_date,
    )

    # Filter by selected date
    filtered_assignments = assignments_df[
        assignments_df["assigned_date_df"].dt.date == selected_date
    ]
    cols = [
        "Item_Id",
        "Destination",
        "Weight(kg)",
        "Available date",
        "Due date",
        "Assigned date",
    ]

    # show date and number of assignments
    st.markdown(
        f"### 📅 Assignments on {selected_date} (Total items to dispatch: {filtered_assignments.shape[0]})"
    )
    filtered_assignments = filtered_assignments.sort_values(
        by=["Destination", "Item_Id"]
    )
    st.dataframe(filtered_assignments[cols], use_container_width=True, width="stretch")
    # button to show the routes on that date
    if st.button("Show routes for selected date"):
        try:
            with open("cvrp_result_main.json", "r") as f:
                raw = json.load(f)

            cvrp_result = {
                date.fromisoformat(d): CVRPOutput.model_validate(r)
                for d, r in raw.items()
            }
            if selected_date in cvrp_result:
                display_cvrp_routes(cvrp_result[selected_date], filtered_assignments)
            else:
                st.warning(f"No CVRP result found for date {selected_date}.")
        except FileNotFoundError:
            st.error("cvrp_result.json not found. Please run the CVRP solver first.")


else:
    st.warning("No assignment data found.")


# --- Daily loads chart ---
if daily_loads:
    daily_loads_df = pd.DataFrame(list(daily_loads.items()), columns=["Date", "Load"])
    st.subheader("⚙️ Daily Loads")
    st.bar_chart(daily_loads_df.set_index("Date"))

