""" Tidy3d package imports"""

from rich import pretty

from .components import BlochBoundary, Symmetry, Periodic, PECBoundary, PMCBoundary
# boundary
from .components import BoundarySpec, Boundary, BoundaryEdge, BoundaryEdgeType
# geometry
from .components import Box, Sphere, Cylinder, PolySlab, GeometryGroup
from .components import DATA_TYPE_MAP, ScalarFieldData, ScalarFieldTimeData
from .components import DefaultPMLParameters, DefaultStablePMLParameters, DefaultAbsorberParameters
# monitors
from .components import FieldMonitor, FieldTimeMonitor, FluxMonitor, FluxTimeMonitor
from .components import GaussianBeam, AstigmaticGaussianBeam
# sources
from .components import GaussianPulse, ContinuousWave
# grid
from .components import Grid, Coords, GridSpec, UniformGrid, CustomGrid, AutoGrid
# medium
from .components import Medium, PoleResidue, AnisotropicMedium, PEC, PECMedium
from .components import ModeData, ModeAmpsData, ModeIndexData, ModeFieldData, PermittivityData
from .components import ModeMonitor, ModeFieldMonitor, PermittivityMonitor
# modes
from .components import ModeSpec
from .components import PML, StablePML, Absorber, PMLParams, AbsorberParams, PMLTypes
from .components import ScalarPermittivityData
from .components import Sellmeier, Debye, Drude, Lorentz
# simulation
from .components import Simulation
# data
from .components import SimulationData, FieldData, FluxData, FluxTimeData
# structures
from .components import Structure
from .components import UniformCurrentSource, PlaneWave, ModeSource, PointDipole
from .components.geometry import Geometry
from .components.grid import YeeGrid, FieldGrid, Coords1D
# for docs
from .components.medium import AbstractMedium
from .components.monitor import Monitor
from .components.source import Source, SourceTime
# constants imported as `C_0 = td.C_0` or `td.constants.C_0`
from .constants import C_0, ETA_0, HBAR, EPSILON_0, MU_0, Q_e, inf
# logging
from .log import log, set_logging_file
# material library dict imported as `from tidy3d import material_library`
# get material `mat` and variant `var` as `material_library[mat][var]`
from .material_library import material_library
# updater
from .updater import Updater
# version
from .version import __version__


def set_logging_level(level: str) -> None:
    """Raise a warning here instead of setting the logging level."""
    raise DeprecationWarning(
        "``set_logging_level`` no longer supported. "
        f"To set the logging level, call ``tidy3d.config.logging_level = {level}``."
    )


# make all stdout and errors pretty

# traceback.install()
