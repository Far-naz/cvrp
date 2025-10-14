from src.data_model.distance import Distance
from src.data_model.factory import Factory
import pandas as pd

def serialize_distance_from_data_frame(df: pd.DataFrame, factories: dict[int, Factory]) -> dict[int, dict[int, float]]:
    C: dict[int, dict[int, float]] = {}

    for _, row in df.iterrows():
        if pd.isna(row.get("Source")) or pd.isna(row.get("Destination")) or pd.isna(row.get("Distance(M)")):
            continue

        try:
            source_id = int(row["Source"].split('_')[1])
            dest_id = int(row["Destination"].split('_')[1])
        except (IndexError, ValueError):
            continue

        if source_id not in factories or dest_id not in factories:
            continue

        distance_m = float(row["Distance(M)"])
        C.setdefault(source_id, {})[dest_id] = distance_m / 1000.0  # convert to km

    return C

