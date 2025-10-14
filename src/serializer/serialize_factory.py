from src.data_model.factory import Factory
import pandas as pd
from typing import Dict
import config


def create_factory_from_data_frame(df: pd.DataFrame) -> Dict[int,Factory]:
    factories: Dict[int, Factory] = {}
    for _, row in df.iterrows():
        
        name_split = str(row['name']).split('_')
        if len(name_split) != 2 or not name_split[1].isdigit():
            raise ValueError(f"Invalid factory name format: {row['name']}")
        
        factory_id = int(name_split[1])
        factory = Factory(
            id=factory_id,
            name=str(row["name"]),
            location=None,
            is_depot=(factory_id == config.DEPOT_ID)
        )
        factories[factory.id] = factory

    return factories
