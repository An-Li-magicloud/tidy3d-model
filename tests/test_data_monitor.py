from tidy3d.components.monitor import FieldMonitor, FieldTimeMonitor, PermittivityMonitor
from tidy3d.components.monitor import ModeFieldMonitor, ModeMonitor
from tidy3d.components.monitor import FluxMonitor, FluxTimeMonitor
from tidy3d.components.mode import ModeSpec

from tidy3d.components.data.monitor_data import FieldData, FieldTimeData, PermittivityData
from tidy3d.components.data.monitor_data import ModeFieldData, ModeData
from tidy3d.components.data.monitor_data import FluxData, FluxTimeData

from .test_data_arrays import make_scalar_field_data_array, make_scalar_field_time_data_array
from .test_data_arrays import make_scalar_mode_field_data_array
from .test_data_arrays import make_flux_data_array, make_flux_time_data_array
from .test_data_arrays import make_mode_amps_data_array, make_mode_index_data_array

# data array instances
FIELD = make_scalar_field_data_array()
FIELD_TIME = make_scalar_field_time_data_array()
MODE_FIELD = make_scalar_mode_field_data_array()
AMPS = make_mode_amps_data_array()
N_COMPLEX = make_mode_index_data_array()
FLUX = make_flux_data_array()
FLUX_TIME = make_flux_time_data_array()

# monitor inputs
SIZE_3D = (1, 1, 1)
SIZE_2D = (1, 0, 1)
MODE_SPEC = ModeSpec(num_modes=4)
FREQS = [1e14, 2e14]
FIELDS = ("Ex", "Ey", "Hz")
INTERVAL = 2

""" Make the montor data """


def make_field_data():
    monitor = FieldMonitor(size=SIZE_3D, fields=FIELDS, name="field", freqs=FREQS)
    return FieldData(monitor=monitor, Ex=FIELD, Ey=FIELD, Hz=FIELD)


def make_field_time_data():
    monitor = FieldTimeMonitor(size=SIZE_3D, fields=FIELDS, name="field_time", interval=INTERVAL)
    return FieldTimeData(monitor=monitor, Ex=FIELD_TIME, Ey=FIELD_TIME, Hz=FIELD_TIME)


def make_mode_field_data():
    monitor = ModeFieldMonitor(size=SIZE_2D, name="mode_field", mode_spec=MODE_SPEC, freqs=FREQS)
    return ModeFieldData(
        monitor=monitor,
        Ex=MODE_FIELD,
        Ey=MODE_FIELD,
        Ez=MODE_FIELD,
        Hx=MODE_FIELD,
        Hy=MODE_FIELD,
        Hz=MODE_FIELD,
    )


def make_permittivity_data():
    monitor = PermittivityMonitor(size=SIZE_3D, name="permittivity", freqs=FREQS)
    return PermittivityData(monitor=monitor, eps_xx=FIELD, eps_yy=FIELD, eps_zz=FIELD)


def make_mode_data():
    monitor = ModeMonitor(size=SIZE_2D, name="mode", mode_spec=MODE_SPEC, freqs=FREQS)
    return ModeData(monitor=monitor, amps=AMPS, n_complex=N_COMPLEX)


def make_flux_data():
    monitor = FluxMonitor(size=SIZE_2D, freqs=FREQS, name="flux")
    return FluxData(monitor=monitor, flux=FLUX)


def make_flux_time_data():
    monitor = FluxTimeMonitor(size=SIZE_2D, interval=INTERVAL, name="flux_time")
    return FluxTimeData(monitor=monitor, flux=FLUX_TIME)


""" Test them out """


def test_field_data():
    data = make_field_data()
    for field in FIELDS:
        _ = getattr(data, field)


def test_field_time_data():
    data = make_field_time_data()
    for field in FIELDS:
        _ = getattr(data, field)


def test_mode_field_data():
    data = make_mode_field_data()
    for field in "EH":
        for comp in "xyz":
            _ = getattr(data, field + comp)


def test_permittivity_data():
    data = make_permittivity_data()
    for comp in "xyz":
        _ = getattr(data, "eps_" + comp + comp)


def test_mode_data():
    data = make_mode_data()
    _ = data.amps
    _ = data.n_complex


def test_flux_data():
    data = make_flux_data()
    _ = data.flux


def test_flux_time_data():
    data = make_flux_time_data()
    _ = data.flux
