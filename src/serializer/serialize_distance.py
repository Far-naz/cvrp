from src.data_model.distance import Distance
from src.data_model.factory import Factory
import pandas as pd

def serialize_distance_from_data_frame(df: pd.DataFrame, factories: dict[str,Factory]) -> dict[tuple[int, int], Distance]:
    distances: dict[tuple[int, int], Distance] = {}
    for _, row in df.iterrows():
        if pd.isna(row.get("Source")) or pd.isna(row.get("Destination")) or pd.isna(row.get("Distance(M)")):
            continue

        source_factory = factories.get(row["Source"])
        destination_factory = factories.get(row["Destination"])
        if source_factory is None or destination_factory is None:
            continue
        distance_instance = Distance(
            source=source_factory,
            destination=destination_factory,
            distance_m=float(row["Distance(M)"])
        )
        distances[(source_factory.id, destination_factory.id)] = distance_instance

    return distances