""" Monitor Level Data, store the DataArrays associated with a single monitor."""
from abc import ABC

import pydantic as pd

from ..monitor import MonitorType, FieldMonitor, FieldTimeMonitor, ModeFieldMonitor
from ..monitor import ModeMonitor, FluxMonitor, FluxTimeMonitor, PermittivityMonitor
from .base import Tidy3dData
from .data_array import ScalarFieldDataArray, ScalarFieldTimeDataArray, ScalarModeFieldDataArray
from .data_array import FluxTimeDataArray, FluxDataArray, ModeIndexDataArray, ModeAmpsDataArray

# TODO: separate validator for field
# TODO: base class for field stuff with symmetry?

class MonitorData(Tidy3dData, ABC):
    """Abstract base class of objects that store data pertaining to a single :class:`.monitor`."""

    monitor: MonitorType


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

    @pd.root_validator(skip_on_failure=True)
    def _contains_fields(cls, values):
        """Make sure the initially specified fields are here."""
        for field_name in values.get("monitor").fields:
            assert values.get(field_name) is not None, f"missing field {field_name}"
        return values


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

    @pd.root_validator(skip_on_failure=True)
    def _contains_fields(cls, values):
        """Make sure the initially specified fields are here."""
        for field_name in values.get("monitor").fields:
            assert values.get(field_name) is not None, f"missing field {field_name}"
        return values


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
