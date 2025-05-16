import numpy as np
import math
from typing import  Tuple
from datetime import datetime
"""
class Point:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z
    
    def to_vector(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])
    
    def distance_to(self, other: 'Point') -> float:
        return np.linalg.norm(self.to_vector() - other.to_vector())
"""

TICKSPERSECOND = 10
TICKSPERCYCLERADAR = 3
TICKSPERCYCLELAUNCHER = 2

def to_integer():
    dt = datetime.today()
    return int(dt.timestamp())

def is_nan_coord(coords: Tuple[float, float, float]) -> bool:
    return any(math.isnan(c) for c in coords)