""" Simulation Level Data """
from typing import Dict

import pydantic as pd

from .base import Tidy3dData
from .monitor_data import MonitorDataType, AbstractFieldData
from ..simulation import Simulation

# TODO: Selecting monitor data using getitem
# TODO: normalization
# TODO: final decay value
# TODO: centering of field data
# TODO: plotting (put some stuff in viz?)
# TODO: saving and loading from hdf5 group or json file
# TODO: docstring examples?
# TODO: getitem
# TODO: at centers
# TODO: ModeSolverData?


class SimulationData(Tidy3dData):
    """Stores data from a collection of :class:`.Monitor` objects in a :class:`.Simulation`."""

    simulation: Simulation = pd.Field(
        ...,
        title="Simulation",
        description="Original :class:`.Simulation` associated with the data.",
    )

    monitor_data: Dict[str, MonitorDataType] = pd.Field(
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

    def __getitem__(self, monitor_name: str) -> MonitorDataType:
        """Get a :class:`.MonitorData` by name. Apply symmetry and normalize if applicable."""

        monitor_data = self.monitor_data[monitor_name]
        grid_expanded = self.simulation.discretize(monitor_data.monitor, extend=True)

        return monitor_data.apply_symmetry(
            symmetry=self.simulation.symmetry,
            symmetry_center=self.simulation.center,
            grid_expanded=grid_expanded,
        )
