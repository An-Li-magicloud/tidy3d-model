from tidy3d.components.simulation import Simulation
from tidy3d.components.grid.grid_spec import GridSpec
from tidy3d.components.data.sim_data import SimulationData
from tidy3d.components.monitor import FieldMonitor, FieldTimeMonitor, ModeFieldMonitor
from tidy3d.components.source import GaussianPulse, PointDipole

from .test_data_monitor import make_field_data, make_field_time_data, make_permittivity_data
from .test_data_monitor import make_mode_data, make_mode_field_data
from .test_data_monitor import make_flux_data, make_flux_time_data
from .utils import clear_tmp

# monitor data instances

FIELD = make_field_data()
FIELD_TIME = make_field_time_data()
PERMITTIVITY = make_permittivity_data()
MODE = make_mode_data()
MODE_FIELD = make_mode_field_data()
FLUX = make_flux_data()
FLUX_TIME = make_flux_time_data()

# for constructing SimulationData

MONITOR_DATA = (FIELD, FIELD_TIME, PERMITTIVITY, MODE, MODE_FIELD, FLUX, FLUX_TIME)
MONITOR_DATA_DICT = {data.monitor.name: data for data in MONITOR_DATA}
MONITORS = [data.monitor for data in MONITOR_DATA]
SOURCES = [PointDipole(source_time=GaussianPulse(freq0=1e14, fwidth=1e14), polarization="Ex")]
SIZE = (2, 2, 2)
GRID_SPEC = GridSpec(wavelength=1.0)
RUN_TIME = 1e-12


def make_sim_data():
    simulation = Simulation(
        monitors=MONITORS, sources=SOURCES, size=SIZE, run_time=RUN_TIME, grid_spec=GRID_SPEC
    )
    return SimulationData(
        simulation=simulation,
        monitor_data=MONITOR_DATA_DICT,
        log="- Time step    827 / time 4.13e-14s (  4 % done), field decay: 0.110e+00",
        normalize_index=None,
    )


def test_sim_data():
    sim_data = make_sim_data()


def test_getitem():
    sim_data = make_sim_data()
    for mon in sim_data.simulation.monitors:
        data = sim_data[mon.name]


def test_centers():
    sim_data = make_sim_data()
    for mon in sim_data.simulation.monitors:
        if isinstance(mon, (FieldMonitor, FieldTimeMonitor, ModeFieldMonitor)):
            data = sim_data.at_centers(mon.name)


def test_plot():
    sim_data = make_sim_data()
    ax = None

    # plot regular field data
    for field_cmp in sim_data.simulation.get_monitor_by_name("field").fields:
        field_data = sim_data["field"].field_components[field_cmp]
        for axis_name in "xyz":
            xyz_kwargs = {axis_name: field_data.coords[axis_name][0]}
            ax = sim_data.plot_field("field", field_cmp, val="real", f=1e14, ax=ax, **xyz_kwargs)
    for axis_name in "xyz":
        xyz_kwargs = {axis_name: 0}
        ax = sim_data.plot_field("field", "int", f=1e14, ax=ax, **xyz_kwargs)

    # plot field time data
    for field_cmp in sim_data.simulation.get_monitor_by_name("field_time").fields:
        field_data = sim_data["field_time"].field_components[field_cmp]
        for axis_name in "xyz":
            xyz_kwargs = {axis_name: field_data.coords[axis_name][0]}
            ax = sim_data.plot_field(
                "field_time", field_cmp, val="real", t=0.0, ax=ax, **xyz_kwargs
            )
    for axis_name in "xyz":
        xyz_kwargs = {axis_name: 0}
        ax = sim_data.plot_field("field_time", "int", t=0.0, ax=ax, **xyz_kwargs)

    # plot mode field data
    for field_cmp in ("Ex", "Ey", "Ez", "Hx", "Hy", "Hz"):
        ax = sim_data.plot_field("mode_field", field_cmp, val="real", f=1e14, mode_index=1, ax=ax)
    ax = sim_data.plot_field("mode_field", "int", f=1e14, mode_index=1, ax=ax)


def test_final_decay():
    sim_data = make_sim_data()
    dv = sim_data.final_decay_value
    assert dv == 0.11


def test_to_json():
    sim_data = make_sim_data()
    j = sim_data.dict()
    sim_data2 = SimulationData(**j)
    assert sim_data == sim_data2
    assert sim_data2["field"].Ex == sim_data["field"].Ex


@clear_tmp
def test_to_hdf5():
    sim_data = make_sim_data()
    sim_data.to_file("tests/tmp/sim_data.hdf5")
    sim_data2 = SimulationData.from_file("tests/tmp/sim_data.hdf5")
