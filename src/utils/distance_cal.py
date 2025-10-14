import math
def compute_travel_days(distance_km: float, truck_speed_kmph: float,
                        load_hours: float = 0.5, unload_hours: float = 0.5,
                        work_hours_per_day: float = 24.0) -> int:
    """
    Returns the number of calendar days a truck will be busy delivering this demand.
    """
    travel_time_hours = distance_km / truck_speed_kmph
    total_hours = travel_time_hours + load_hours + unload_hours
    return max(1, int(math.ceil(total_hours / work_hours_per_day)))