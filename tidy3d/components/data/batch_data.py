""" Batch Level Data """
from typing import Dict

from .base import Tidy3dData
from .sim_data import SimulationData

# TODO: iterating through batch data

class BatchData(Tidy3dData):
    """Collection of :class:`.SimulationData` objects."""

    sim_data_dict: Dict[str, SimulationData]
