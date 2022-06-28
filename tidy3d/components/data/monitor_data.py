""" Monitor Level Data, store the DataArrays associated with a single monitor."""
from abc import ABC
from typing import Union, Dict
from typing_extensions import Annotated

import pydantic as pd

from ..base import TYPE_TAG_STR
from ..monitor import Monitor, MonitorType, FieldMonitor, FieldTimeMonitor, ModeFieldMonitor
from ..monitor import ModeMonitor, FluxMonitor, FluxTimeMonitor, PermittivityMonitor
from ..validators import enforce_monitor_fields_present

from .base import Tidy3dData
from .data_array import ScalarFieldDataArray, ScalarFieldTimeDataArray, ScalarModeFieldDataArray
from .data_array import FluxTimeDataArray, FluxDataArray, ModeIndexDataArray, ModeAmpsDataArray

# TODO: base class for field objects?
# TODO: saving and loading from hdf5 group or json file
# TODO: field data colocate
# TODO: mode data neff, keff properties
# TODO: docstring examples?
# TODO: ModeFieldData select by index -> FieldData
# TODO: equality checking two MonitorData


class MonitorData(Tidy3dData, ABC):
    """Abstract base class of objects that store data pertaining to a single :class:`.monitor`."""

    monitor: MonitorType = pd.Field(
        ...,
        title="Monitor",
        description="Monitor associated with the data.",
        descriminator=TYPE_TAG_STR,
    )

    def expand_symmetry(grid, center) -> "Self":
        """Return copy of self with symmetry applied. If None, flags that data is unaffected."""
        return None

    def normalize(self, source_freq_amps) -> "Self":
        """Return copy of self after normalization is applied using source spectrum."""
        if self.normalized:
            raise ValueError("object already normalized")
        return None


# class AbstractField(MonitorData, ABC):
#     """Collection of scalar fields with some symmetry properties."""
#     monitor: Union[FieldMonitor, FieldTimeMonitor, PermittivityMonitor, ModeFieldMonitor]


class FieldData(MonitorData):
    """Data associated with a :class:`.FieldMonitor`: scalar components of E and H fields."""

    monitor: FieldMonitor

    Ex: ScalarFieldDataArray = pd.Field(
        None,
        title="Ex",
        description="Spatial distribution of the x-component of the electric field.",
    )
    Ey: ScalarFieldDataArray = pd.Field(
        None,
        title="Ey",
        description="Spatial distribution of the y-component of the electric field.",
    )
    Ez: ScalarFieldDataArray = pd.Field(
        None,
        title="Ez",
        description="Spatial distribution of the z-component of the electric field.",
    )
    Hx: ScalarFieldDataArray = pd.Field(
        None,
        title="Hx",
        description="Spatial distribution of the x-component of the magnetic field.",
    )
    Hy: ScalarFieldDataArray = pd.Field(
        None,
        title="Hy",
        description="Spatial distribution of the y-component of the magnetic field.",
    )
    Hz: ScalarFieldDataArray = pd.Field(
        None,
        title="Hz",
        description="Spatial distribution of the z-component of the magnetic field.",
    )

    _contains_monitor_fields = enforce_monitor_fields_present()


class FieldTimeData(MonitorData):
    """Data associated with a :class:`.FieldTimeMonitor`: scalar components of E and H fields."""

    monitor: FieldTimeMonitor

    Ex: ScalarFieldTimeDataArray = pd.Field(
        None,
        title="Ex",
        description="Spatial distribution of the x-component of the electric field.",
    )
    Ey: ScalarFieldTimeDataArray = pd.Field(
        None,
        title="Ey",
        description="Spatial distribution of the y-component of the electric field.",
    )
    Ez: ScalarFieldTimeDataArray = pd.Field(
        None,
        title="Ez",
        description="Spatial distribution of the z-component of the electric field.",
    )
    Hx: ScalarFieldTimeDataArray = pd.Field(
        None,
        title="Hx",
        description="Spatial distribution of the x-component of the magnetic field.",
    )
    Hy: ScalarFieldTimeDataArray = pd.Field(
        None,
        title="Hy",
        description="Spatial distribution of the y-component of the magnetic field.",
    )
    Hz: ScalarFieldTimeDataArray = pd.Field(
        None,
        title="Hz",
        description="Spatial distribution of the z-component of the magnetic field.",
    )

    _contains_monitor_fields = enforce_monitor_fields_present()


class PermittivityData(MonitorData):
    """Data for a :class:`.PermittivityMonitor`: diagonal components of the permittivity tensor."""

    monitor: PermittivityMonitor

    eps_xx: ScalarFieldDataArray = pd.Field(
        ...,
        title="Epsilon xx",
        description="Spatial distribution of the x-component of the electric field.",
    )
    eps_yy: ScalarFieldDataArray = pd.Field(
        ...,
        title="Epsilon yy",
        description="Spatial distribution of the y-component of the electric field.",
    )
    eps_zz: ScalarFieldDataArray = pd.Field(
        ...,
        title="Epsilon zz",
        description="Spatial distribution of the z-component of the electric field.",
    )


class ModeFieldData(MonitorData):
    """Data associated with a :class:`.ModeFieldMonitor`: scalar components of E and H fields."""

    monitor: ModeFieldMonitor

    Ex: ScalarModeFieldDataArray = pd.Field(
        ...,
        title="Ex",
        description="Spatial distribution of the x-component of the electric field of the mode.",
    )
    Ey: ScalarModeFieldDataArray = pd.Field(
        ...,
        title="Ey",
        description="Spatial distribution of the y-component of the electric field of the mode.",
    )
    Ez: ScalarModeFieldDataArray = pd.Field(
        ...,
        title="Ez",
        description="Spatial distribution of the z-component of the electric field of the mode.",
    )
    Hx: ScalarModeFieldDataArray = pd.Field(
        ...,
        title="Hx",
        description="Spatial distribution of the x-component of the magnetic field of the mode.",
    )
    Hy: ScalarModeFieldDataArray = pd.Field(
        ...,
        title="Hy",
        description="Spatial distribution of the y-component of the magnetic field of the mode.",
    )
    Hz: ScalarModeFieldDataArray = pd.Field(
        ...,
        title="Hz",
        description="Spatial distribution of the z-component of the magnetic field of the mode.",
    )


class ModeData(MonitorData):
    """Data associated with a :class:`.ModeMonitor`: modal amplitudes and propagation indices."""

    monitor: ModeMonitor
    amps: ModeAmpsDataArray = pd.Field(
        ..., title="Amplitudes", description="Complex-valued amplitudes associated with the mode."
    )
    n_complex: ModeIndexDataArray = pd.Field(
        ...,
        title="Amplitudes",
        description="Complex-valued effective propagation constants associated with the mode.",
    )


class FluxData(MonitorData):
    """Data associated with a :class:`.FluxMonitor`: flux data in the frequency-domain."""

    monitor: FluxMonitor
    flux: FluxDataArray


class FluxTimeData(MonitorData):
    """Data associated with a :class:`.FluxTimeMonitor`: flux data in the time-domain."""

    monitor: FluxTimeMonitor
    flux: FluxTimeDataArray


MonitorDataType = Annotated[
    Union[
        FieldData, FieldTimeData, PermittivityData, ModeFieldData, ModeData, FluxData, FluxTimeData
    ],
    pd.Field(discriminator=TYPE_TAG_STR),
]
