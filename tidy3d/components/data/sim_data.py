""" Simulation Level Data """
from typing import Dict

import pydantic as pd

from .base import Tidy3dData
from .monitor_data import MonitorData
from ..simulation import Simulation

# TODO: Selecting monitor data using getitem
# TODO: normalization
# TODO: final decay value
# TODO: centering of field data
# TODO: plotting

class SimulationData(Tidy3dData):
    """Stores data from a collection of :class:`.Monitor` objects in a :class:`.Simulation`."""
    simulation: Simulation
    monitor_data: Dict[str, MonitorData]

    simulation: Simulation = pd.Field(
        ...,
        title="Simulation",
        description="Original :class:`.Simulation` associated with the data.",
    )

    monitor_data: Dict[str, Tidy3dData] = pd.Field(
        ...,
        title="Monitor Data",
        description="Mapping of monitor name to :class:`.MonitorData` instance.",
    )

    log: str = pd.Field(
        None,
        title="Solver Log",
        description="A string containing the log information from the simulation run.",
    )

    diverged: bool = pd.Field(
        False,
        title="Diverged",
        description="A boolean flag denoting whether the simulation run diverged.",
    )