from pydantic import BaseModel
from src.data_model.factory import Factory
    
from typing import List
import numpy as np

class Distance(BaseModel):
    source: Factory
    destination: Factory
    distance_m: float

    @staticmethod
    def distance_in_km(distance_m: float) -> float:
        return distance_m / 1000


def build_distance_matrix(distances: List[Distance], factories: list[Factory]) -> List[List[float]]:
    """
    Convert list of Distance objects into a 2D distance matrix
    Index of factories in the matrix matches their position in 'factories' list.
    """
    n = len(factories)
    # Map factory id to matrix index
    factory_idx = {factory.id: idx for idx, factory in enumerate(factories)}

    # Initialize matrix with large value for unreachable pairs
    matrix = np.full((n, n), np.inf)

    for dist in distances:
        i = factory_idx[dist.source]
        j = factory_idx[dist.destination]
        matrix[i][j] = Distance.distance_in_km(dist.distance_m)

    # Optional: set diagonal to 0
    np.fill_diagonal(matrix, 0.0)
    return matrix.tolist()

