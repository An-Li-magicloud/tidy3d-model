"""Near field to far field transformation plugin
"""
from typing import Dict, Tuple, Union, List
import numpy as np
import xarray as xr
import pydantic

from rich.progress import track

from ...constants import C_0, ETA_0, MICROMETER
from ...components.data import FieldData, SimulationData, Near2FarData, RadiationVector
from ...components.monitor import FieldMonitor
from ...components.types import Direction, Axis, Coordinate, ArrayLike
from ...components.medium import Medium
from ...components.base import Tidy3dBaseModel, cached_property
from ...log import SetupError, ValidationError

# Default number of points per wavelength in the background medium to use for resampling fields.
PTS_PER_WVL = 10

# Numpy float array and related array types
ArrayLikeN2F = Union[float, Tuple[float, ...], ArrayLike[float, 4]]


class Near2FarSurface(Tidy3dBaseModel):
    """Data structure to store surface monitor data with associated surface current densities."""

    monitor: FieldMonitor = pydantic.Field(
        ...,
        title="Near field monitor",
        description=":class:`.FieldMonitor` on which near fields will be sampled and integrated.",
    )

    normal_dir: Direction = pydantic.Field(
        ...,
        title="Normal vector orientation",
        description=":class:`.Direction` of the surface monitor's normal vector w.r.t. "
        "the positive x, y or z unit vectors. Must be one of '+' or '-'.",
    )

    @cached_property
    def axis(self) -> Axis:
        """Returns the :class:`.Axis` normal to this surface."""
        # assume that the monitor's axis is in the direction where the monitor is thinnest
        return self.monitor.size.index(0.0)

    @pydantic.validator("monitor", always=True)
    def is_plane(cls, val):
        """Ensures that the monitor is a plane, i.e., its `size` attribute has exactly 1 zero"""
        size = val.size
        if size.count(0.0) != 1 and isinstance(val, FieldMonitor):
            raise ValidationError(f"Monitor '{val.name}' must be planar, given size={size}")
        return val


class Near2Far(Tidy3dBaseModel):
    """Near field to far field transformation tool."""

    sim_data: SimulationData = pydantic.Field(
        ...,
        title="Simulation data",
        description="Container for simulation data containing the near field monitors.",
    )

    surfaces: Tuple[Near2FarSurface, ...] = pydantic.Field(
        None,
        title="Surface monitor with direction",
        description="Tuple of each :class:`.Near2FarSurface` to use as source of near field.",
    )

    resample: bool = pydantic.Field(
        True,
        title="Resample surface currents",
        description="Pick whether to resample surface currents based on ``pts_per_wavelength``. "
        "If ``False``, the field ``pts_per_wavelength`` has no effect.",
    )

    pts_per_wavelength: int = pydantic.Field(
        PTS_PER_WVL,
        title="Points per wavelength",
        description="Number of points per wavelength in the background medium with which "
        "to discretize the surface monitors for the projection.",
    )

    medium: Medium = pydantic.Field(
        None,
        title="Background medium",
        description="Background medium in which to radiate near fields to far fields. "
        "If ``None``, uses the :class:.Simulation background medium.",
    )

    origin: Coordinate = pydantic.Field(
        None,
        title="Local origin",
        description="Local origin used for defining observation points. If ``None``, uses the "
        "average of the centers of all surface monitors.",
        units=MICROMETER,
    )

    currents: Dict[str, xr.Dataset] = pydantic.Field(
        None,
        title="Surface current densities",
        description="Dictionary mapping monitor name to an ``xarray.Dataset`` storing the "
        "surface current densities.",
    )

    @pydantic.validator("origin", always=True)
    def set_origin(cls, val, values):
        """Sets .origin as the average of centers of all surface monitors if not provided."""
        if val is None:
            surfaces = values.get("surfaces")
            val = np.array([surface.monitor.center for surface in surfaces])
            return tuple(np.mean(val, axis=0))
        return val

    @pydantic.validator("medium", always=True)
    def set_medium(cls, val, values):
        """Sets the .medium field using the simulation default if no medium was provided."""
        if val is None:
            val = values.get("sim_data").simulation.medium
        return val

    @cached_property
    def frequencies(self) -> List[float]:
        """Return the list of frequencies associated with the field monitors."""
        return self.surfaces[0].monitor.freqs

    def nk(self, frequency) -> Tuple[float, float]:
        """Returns the real and imaginary parts of the background medium's refractive index."""
        eps_complex = self.medium.eps_model(frequency)
        return self.medium.eps_complex_to_nk(eps_complex)

    def k(self, frequency) -> complex:
        """Returns the complex wave number associated with the background medium."""
        index_n, index_k = self.nk(frequency)
        return (2 * np.pi * frequency / C_0) * (index_n + 1j * index_k)

    def eta(self, frequency) -> complex:
        """Returns the complex wave impedance associated with the background medium."""
        index_n, index_k = self.nk(frequency)
        return ETA_0 / (index_n + 1j * index_k)

    @classmethod
    # pylint:disable=too-many-arguments
    def from_near_field_monitors(
        cls,
        sim_data: SimulationData,
        monitors: List[FieldMonitor],
        normal_dirs: List[Direction],
        resample: bool = True,
        pts_per_wavelength: int = PTS_PER_WVL,
        medium: Medium = None,
        origin: Coordinate = None,
    ):
        """Constructs :class:`Near2Far` from a list of near field monitors and their directions.

        Parameters
        ----------
        sim_data : :class:`.SimulationData`
            Container for simulation data containing the near field monitors.
        monitors : List[:class:`.FieldMonitor`]
            Tuple of :class:`.FieldMonitor` objects on which near fields will be sampled.
        normal_dirs : List[:class:`.Direction`]
            Tuple containing the :class:`.Direction` of the normal to each surface monitor
            w.r.t. to the positive x, y or z unit vectors. Must have the same length as monitors.
        resample : bool = True
            Pick whether to resample surface currents based on ``pts_per_wavelength``.
            "If ``False``, the argument ``pts_per_wavelength`` has no effect.
        pts_per_wavelength : int = 10
            Number of points per wavelength with which to discretize the
            surface monitors for the projection.
        medium : :class:`.Medium`
            Background medium in which to radiate near fields to far fields.
            Default: same as the :class:`.Simulation` background medium.
        origin : :class:`.Coordinate`
            Local origin used for defining observation points. If ``None``, uses the
            average of the centers of all surface monitors.
        """

        if len(monitors) != len(normal_dirs):
            raise SetupError(
                f"Number of monitors ({len(monitors)}) does not equal "
                "the number of directions ({len(normal_dirs)})."
            )

        surfaces = [
            Near2FarSurface(monitor=monitor, normal_dir=normal_dir)
            for monitor, normal_dir in zip(monitors, normal_dirs)
        ]

        return cls(
            sim_data=sim_data,
            surfaces=surfaces,
            resample=resample,
            pts_per_wavelength=pts_per_wavelength,
            medium=medium,
            origin=origin,
        )

    @cached_property
    def currents(self):
        """Sets the surface currents."""
        sim_data = self.sim_data
        surfaces = self.surfaces
        resample = self.resample
        pts_per_wavelength = self.pts_per_wavelength
        medium = self.medium

        if surfaces is None:
            return None

        surface_currents = {}
        for surface in surfaces:
            current_data = self.compute_surface_currents(
                sim_data, surface, medium, resample, pts_per_wavelength
            )
            surface_currents[surface.monitor.name] = current_data

        return surface_currents

    @staticmethod
    # pylint:disable=too-many-arguments
    def compute_surface_currents(
        sim_data: SimulationData,
        surface: Near2FarSurface,
        medium: Medium,
        resample: bool = True,
        pts_per_wavelength: int = PTS_PER_WVL,
    ) -> xr.Dataset:
        """Returns resampled surface current densities associated with the surface monitor.

        Parameters
        ----------
        sim_data : :class:`.SimulationData`
            Container for simulation data containing the near field monitors.
        surface: :class:`.Near2FarSurface`
            :class:`.Near2FarSurface` to use as source of near field.
        medium : :class:`.Medium`
            Background medium in which to radiate near fields to far fields.
            Default: same as the :class:`.Simulation` background medium.
        resample : bool = True
            Pick whether to resample surface currents based on ``pts_per_wavelength``.
            "If ``False``, the argument ``pts_per_wavelength`` has no effect.
        pts_per_wavelength : int = 10
            Number of points per wavelength with which to discretize the
            surface monitors for the projection.

        Returns
        -------
        xarray.Dataset
            Colocated surface current densities for the given surface.
        """

        monitor_name = surface.monitor.name
        if monitor_name not in sim_data.monitor_data.keys():
            raise SetupError(f"No data for monitor named '{monitor_name}' found in sim_data.")

        field_data = sim_data[monitor_name]

        currents = Near2Far._fields_to_currents(field_data, surface)
        currents = Near2Far._resample_surface_currents(
            currents, sim_data, surface, medium, resample, pts_per_wavelength
        )

        return currents

    @staticmethod
    def _fields_to_currents(  # pylint:disable=too-many-locals
        field_data: FieldData, surface: Near2FarSurface
    ) -> FieldData:
        """Returns surface current densities associated with a given :class:`.FieldData` object.

        Parameters
        ----------
        field_data : :class:`.FieldData`
            Container for field data associated with the given near field surface.
        surface: :class:`.Near2FarSurface`
            :class:`.Near2FarSurface` to use as source of near field.

        Returns
        -------
        :class:`.FieldData`
            Surface current densities for the given surface.
        """

        # figure out which field components are tangential or normal to the monitor
        normal_field, tangent_fields = surface.monitor.pop_axis(("x", "y", "z"), axis=surface.axis)

        signs = np.array([-1, 1])
        if surface.axis % 2 != 0:
            signs *= -1
        if surface.normal_dir == "-":
            signs *= -1

        # compute surface current densities and delete unneeded field components
        cmp_1, cmp_2 = tangent_fields

        J1 = "J" + cmp_1
        J2 = "J" + cmp_2
        M1 = "M" + cmp_1
        M2 = "M" + cmp_2
        E1 = "E" + cmp_1
        E2 = "E" + cmp_2
        H1 = "H" + cmp_1
        H2 = "H" + cmp_2
        E_normal = "E" + normal_field
        H_normal = "H" + normal_field

        currents = field_data.copy()

        currents.data_dict[J2] = currents.data_dict.pop(H1)
        currents.data_dict[J1] = currents.data_dict.pop(H2)
        del currents.data_dict[H_normal]

        currents.data_dict[M2] = currents.data_dict.pop(E1)
        currents.data_dict[M1] = currents.data_dict.pop(E2)
        del currents.data_dict[E_normal]

        new_values_J1 = currents.data_dict[J1].values * signs[0]
        new_values_J2 = currents.data_dict[J2].values * signs[1]

        new_values_M1 = currents.data_dict[M1].values * signs[1]
        new_values_M2 = currents.data_dict[M2].values * signs[0]

        currents.data_dict[J1] = currents.data_dict[J1].copy(update=dict(values=new_values_J1))
        currents.data_dict[J2] = currents.data_dict[J2].copy(update=dict(values=new_values_J2))
        currents.data_dict[M1] = currents.data_dict[M1].copy(update=dict(values=new_values_M1))
        currents.data_dict[M2] = currents.data_dict[M2].copy(update=dict(values=new_values_M2))

        return currents

    @staticmethod
    # pylint:disable=too-many-locals, too-many-arguments
    def _resample_surface_currents(
        currents: xr.Dataset,
        sim_data: SimulationData,
        surface: Near2FarSurface,
        medium: Medium,
        resample: bool = True,
        pts_per_wavelength: int = PTS_PER_WVL,
    ) -> xr.Dataset:
        """Returns the surface current densities associated with the surface monitor.

        Parameters
        ----------
        currents : xarray.Dataset
            Surface currents defined on the original Yee grid.
        sim_data : :class:`.SimulationData`
            Container for simulation data containing the near field monitors.
        surface: :class:`.Near2FarSurface`
            :class:`.Near2FarSurface` to use as source of near field.
        medium : :class:`.Medium`
            Background medium in which to radiate near fields to far fields.
            Default: same as the :class:`.Simulation` background medium.
        resample : bool = True
            Pick whether to resample surface currents based on ``pts_per_wavelength``.
            "If ``False``, the argument ``pts_per_wavelength`` has no effect.
        pts_per_wavelength : int = 10
            Number of points per wavelength with which to discretize the
            surface monitors for the projection.

        Returns
        -------
        xarray.Dataset
            Colocated surface current densities for the given surface.
        """

        # colocate surface currents on a regular grid of points on the monitor based on wavelength
        colocation_points = [None] * 3
        colocation_points[surface.axis] = surface.monitor.center[surface.axis]

        # use the highest frequency associated with the monitor to resample the surface currents
        frequency = max(surface.monitor.freqs)
        eps_complex = medium.eps_model(frequency)
        index_n, _ = medium.eps_complex_to_nk(eps_complex)
        wavelength = C_0 / frequency / index_n

        _, idx_uv = surface.monitor.pop_axis((0, 1, 2), axis=surface.axis)

        for idx in idx_uv:

            if not resample:
                comp = ["x", "y", "z"][idx]
                colocation_points[idx] = sim_data.at_centers(surface.monitor.name)[comp].values
                continue

            # pick sample points on the monitor and handle the possibility of an "infinite" monitor
            start = np.maximum(
                surface.monitor.center[idx] - surface.monitor.size[idx] / 2.0,
                sim_data.simulation.center[idx] - sim_data.simulation.size[idx] / 2.0,
            )
            stop = np.minimum(
                surface.monitor.center[idx] + surface.monitor.size[idx] / 2.0,
                sim_data.simulation.center[idx] + sim_data.simulation.size[idx] / 2.0,
            )
            size = stop - start

            num_pts = int(np.ceil(pts_per_wavelength * size / wavelength))
            points = np.linspace(start, stop, num_pts)
            colocation_points[idx] = points

        currents = currents.colocate(*colocation_points)
        return currents

    # pylint:disable=too-many-locals, too-many-arguments
    def _radiation_vectors_for_surface(
        self,
        frequency: float,
        theta: ArrayLikeN2F,
        phi: ArrayLikeN2F,
        surface: Near2FarSurface,
        currents: xr.Dataset,
    ):
        """Compute radiation vectors at an angle in spherical coordinates
        for a given set of surface currents and observation angles.

        Parameters
        ----------
        frequency : float
            Frequency to select from each :class:`.FieldMonitor` to use for projection.
            Must be a frequency stored in each :class:`FieldMonitor`.
        theta : Union[float, Tuple[float, ...], np.ndarray]
            Polar angles (rad) downward from x=y=0 line relative to the local origin.
        phi : Union[float, Tuple[float, ...], np.ndarray]
            Azimuthal (rad) angles from y=z=0 line relative to the local origin.
        surface: :class:`Near2FarSurface`
            :class:`Near2FarSurface` object to use as source of near field.
        currents : xarray.Dataset
            xarray Dataset containing surface currents associated with the surface monitor.

        Returns
        -------
        tuple(numpy.ndarray[float],numpy.ndarray[float],numpy.ndarray[float],numpy.ndarray[float])
            ``N_theta``, ``N_phi``, ``L_theta``, ``L_phi`` radiation vectors for the given surface.
        """

        # make sure that observation points are interpreted w.r.t. the local origin
        pts = [currents[name].values - origin for name, origin in zip(["x", "y", "z"], self.origin)]

        try:
            currents_f = currents.sel(f=frequency)
        except Exception as e:
            raise SetupError(
                f"Frequency {frequency} not found in fields for monitor '{surface.monitor.name}'."
            ) from e

        idx_w, idx_uv = surface.monitor.pop_axis((0, 1, 2), axis=surface.axis)
        _, source_names = surface.monitor.pop_axis(("x", "y", "z"), axis=surface.axis)

        idx_u, idx_v = idx_uv
        cmp_1, cmp_2 = source_names

        theta = np.atleast_1d(theta)
        phi = np.atleast_1d(phi)

        sin_theta = np.sin(theta)
        cos_theta = np.cos(theta)
        sin_phi = np.sin(phi)
        cos_phi = np.cos(phi)

        J = np.zeros((3, len(theta), len(phi)), dtype=complex)
        M = np.zeros_like(J)

        def integrate_2d(function, pts_u, pts_v):
            """Trapezoidal integration in two dimensions."""
            return np.trapz(np.trapz(function, pts_u, axis=0), pts_v, axis=0)

        phase = [None] * 3
        propagation_factor = -1j * self.k(frequency)

        def integrate_for_one_theta(i_th: int):
            """Perform integration for a given theta angle index"""

            for j_ph in np.arange(len(phi)):

                phase[0] = np.exp(propagation_factor * pts[0] * sin_theta[i_th] * cos_phi[j_ph])
                phase[1] = np.exp(propagation_factor * pts[1] * sin_theta[i_th] * sin_phi[j_ph])
                phase[2] = np.exp(propagation_factor * pts[2] * cos_theta[i_th])

                phase_ij = phase[idx_u][:, None] * phase[idx_v][None, :] * phase[idx_w]

                J[idx_u, i_th, j_ph] = integrate_2d(
                    currents_f[f"J{cmp_1}"].values * phase_ij, pts[idx_u], pts[idx_v]
                )

                J[idx_v, i_th, j_ph] = integrate_2d(
                    currents_f[f"J{cmp_2}"].values * phase_ij, pts[idx_u], pts[idx_v]
                )

                M[idx_u, i_th, j_ph] = integrate_2d(
                    currents_f[f"M{cmp_1}"].values * phase_ij, pts[idx_u], pts[idx_v]
                )

                M[idx_v, i_th, j_ph] = integrate_2d(
                    currents_f[f"M{cmp_2}"].values * phase_ij, pts[idx_u], pts[idx_v]
                )

        if len(theta) < 2:
            integrate_for_one_theta(0)
        else:
            for i_th in track(
                np.arange(len(theta)),
                description=f"Processing surface monitor '{surface.monitor.name}'...",
            ):
                integrate_for_one_theta(i_th)

        cos_th_cos_phi = cos_theta[:, None] * cos_phi[None, :]
        cos_th_sin_phi = cos_theta[:, None] * sin_phi[None, :]

        # N_theta (8.33a)
        N_theta = J[0] * cos_th_cos_phi + J[1] * cos_th_sin_phi - J[2] * sin_theta[:, None]

        # N_phi (8.33b)
        N_phi = -J[0] * sin_phi[None, :] + J[1] * cos_phi[None, :]

        # L_theta  (8.34a)
        L_theta = M[0] * cos_th_cos_phi + M[1] * cos_th_sin_phi - M[2] * sin_theta[:, None]

        # L_phi  (8.34b)
        L_phi = -M[0] * sin_phi[None, :] + M[1] * cos_phi[None, :]

        return N_theta, N_phi, L_theta, L_phi

    def radiation_vectors(self, theta: ArrayLikeN2F, phi: ArrayLikeN2F) -> Near2FarData:
        """Compute radiation vectors at given angles in spherical coordinates.

        Parameters
        ----------
        theta : Union[float, Tuple[float, ...], np.ndarray]
            Polar angles (rad) downward from x=y=0 line relative to the local origin.
        phi : Union[float, Tuple[float, ...], np.ndarray]
            Azimuthal (rad) angles from y=z=0 line relative to the local origin.

        Returns
        -------
        :class:.`Near2FarData`
            Data structure with ``N_theta``, ``N_phi``, ``L_theta``, ``L_phi`` radiation vectors.
        """

        freqs = self.frequencies

        # compute radiation vectors for the dataset associated with each monitor
        N_theta = np.zeros((len(theta), len(phi), len(freqs)), dtype=complex)
        N_phi = np.zeros_like(N_theta)
        L_theta = np.zeros_like(N_theta)
        L_phi = np.zeros_like(N_theta)

        for idx_f, frequency in enumerate(freqs):
            for surface in self.surfaces:
                _N_th, _N_ph, _L_th, _L_ph = self._radiation_vectors_for_surface(
                    frequency, theta, phi, surface, self.currents[surface.monitor.name]
                )
                N_theta[..., idx_f] += _N_th
                N_phi[..., idx_f] += _N_ph
                L_theta[..., idx_f] += _L_th
                L_phi[..., idx_f] += _L_ph

        nth = RadiationVector(values=N_theta, theta=theta, phi=phi, f=freqs)
        nph = RadiationVector(values=N_phi, theta=theta, phi=phi, f=freqs)
        lth = RadiationVector(values=L_theta, theta=theta, phi=phi, f=freqs)
        lph = RadiationVector(values=L_phi, theta=theta, phi=phi, f=freqs)

        return Near2FarData(data_dict={"Ntheta": nth, "Nphi": nph, "Ltheta": lth, "Lphi": lph})

    # def fields_spherical(self, r: float, theta: ArrayLikeN2F, phi: ArrayLikeN2F) -> xr.Dataset:
    #     """Get fields at a point relative to monitor center in spherical coordinates.

    #     Parameters
    #     ----------
    #     r : float
    #         (micron) radial distance relative to monitor center.
    #     theta : Union[float, Tuple[float, ...], np.ndarray]
    #         (radian) polar angles downward from x=y=0 relative to the local origin.
    #     phi : Union[float, Tuple[float, ...], np.ndarray]
    #         (radian) azimuthal angles from y=z=0 line relative to the local origin.

    #     Returns
    #     -------
    #     xarray.Dataset
    #         xarray dataset containing (Er, Etheta, Ephi), (Hr, Htheta, Hphi)
    #         in polar coordinates.
    #     """

    #     theta = np.atleast_1d(theta)
    #     phi = np.atleast_1d(phi)

    #     # project radiation vectors to distance r away for given angles
    #     rad_vecs = self._radiation_vectors(theta, phi)

    #     k = np.array([self.k(frequency) for frequency in self.frequencies])
    #     scalar_proj_r = (
    #         -self.phasor_positive_sign
    #         * 1j
    #         * k
    #         * np.exp(self.phasor_positive_sign * 1j * k * r)
    #         / (4 * np.pi * r)
    #     )
    #     scalar_proj_r = scalar_proj_r[None, None, ...]

    #     eta = np.array([self.eta(frequency) for frequency in self.frequencies])
    #     eta = eta[None, None, ...]

    #     # assemble E felds
    #     Et_array = -scalar_proj_r * (rad_vecs.Lphi.values + eta * rad_vecs.Ntheta.values)
    #     Ep_array = scalar_proj_r * (rad_vecs.Ltheta.values - eta * rad_vecs.Nphi.values)
    #     Er_array = np.zeros_like(Ep_array)

    #     # assemble H fields
    #     Ht_array = -Ep_array / eta
    #     Hp_array = Et_array / eta
    #     Hr_array = np.zeros_like(Hp_array)

    #     dims = ("r", "theta", "phi", "f")
    #     coords = {"r": [r], "theta": theta, "phi": phi, "f": self.frequencies}

    #     Er = xr.DataArray(data=Er_array[None, ...], coords=coords, dims=dims)
    #     Et = xr.DataArray(data=Et_array[None, ...], coords=coords, dims=dims)
    #     Ep = xr.DataArray(data=Ep_array[None, ...], coords=coords, dims=dims)

    #     Hr = xr.DataArray(data=Hr_array[None, ...], coords=coords, dims=dims)
    #     Ht = xr.DataArray(data=Ht_array[None, ...], coords=coords, dims=dims)
    #     Hp = xr.DataArray(data=Hp_array[None, ...], coords=coords, dims=dims)

    #     return xr.Dataset(
    #         {"E_r": Er, "E_theta": Et, "E_phi": Ep, "H_r": Hr, "H_theta": Ht, "H_phi": Hp}
    #     )

    # def radar_cross_section(self, theta: ArrayLikeN2F, phi: ArrayLikeN2F) -> xr.DataArray:
    #     """Get radar cross section at a point relative to the local origin in
    #     units of incident power.

    #     Parameters
    #     ----------
    #     theta : Union[float, List[float], np.ndarray]
    #         (radian) polar angles downward from x=y=0 relative to the local origin.
    #     phi : Union[float, List[float], np.ndarray]
    #         (radian) azimuthal angles from y=z=0 line relative to the local origin.

    #     Returns
    #     -------
    #     RCS : xarray.DataArray
    #         Radar cross section at angles relative to the local origin.
    #     """

    #     theta = np.atleast_1d(theta)
    #     phi = np.atleast_1d(phi)

    #     for frequency in self.frequencies:
    #         _, index_k = self.nk(frequency)
    #         if index_k != 0.0:
    #             raise SetupError("Can't compute RCS for a lossy background medium.")

    #     k = np.array([self.k(frequency) for frequency in self.frequencies])
    #     eta = np.array([self.eta(frequency) for frequency in self.frequencies])

    #     k = k[None, None, ...]
    #     eta = eta[None, None, ...]

    #     rad_vecs = self._radiation_vectors(theta, phi)

    #     constant = k**2 / (8 * np.pi * eta)
    #     term1 = np.abs(rad_vecs.Lphi.values + eta * rad_vecs.Ntheta.values) ** 2
    #     term2 = np.abs(rad_vecs.Ltheta.values - eta * rad_vecs.Nphi.values) ** 2
    #     rcs_data = constant * (term1 + term2)

    #     dims = ("theta", "phi", "f")
    #     coords = {"theta": theta, "phi": phi, "f": self.frequencies}

    #     return xr.DataArray(data=rcs_data, coords=coords, dims=dims)

    # def power_spherical(self, r: float, theta: ArrayLikeN2F, phi: ArrayLikeN2F) -> xr.DataArray:
    #     """Get power scattered to a point relative to the local origin in spherical coordinates.

    #     Parameters
    #     ----------
    #     r : float
    #         (micron) radial distance relative to the local origin.
    #     theta : Union[float, Tuple[float, ...], np.ndarray]
    #         (radian) polar angles downward from x=y=0 relative to the local origin.
    #     phi : Union[float, Tuple[float, ...], np.ndarray]
    #         (radian) azimuthal angles from y=z=0 line relative to the local origin.

    #     Returns
    #     -------
    #     power : xarray.DataArray
    #         Power at points relative to the local origin.
    #     """

    #     theta = np.atleast_1d(theta)
    #     phi = np.atleast_1d(phi)

    #     field_data = self.fields_spherical(r, theta, phi)
    #     Et, Ep = [field_data[comp].values for comp in ["E_theta", "E_phi"]]
    #     Ht, Hp = [field_data[comp].values for comp in ["H_theta", "H_phi"]]
    #     power_theta = 0.5 * np.real(Et * np.conj(Hp))
    #     power_phi = 0.5 * np.real(-Ep * np.conj(Ht))
    #     power_data = power_theta + power_phi

    #     dims = ("r", "theta", "phi", "f")
    #     coords = {"r": [r], "theta": theta, "phi": phi, "f": self.frequencies}

    #     return xr.DataArray(data=power_data, coords=coords, dims=dims)

    # def fields_cartesian(self, x: ArrayLikeN2F, y: ArrayLikeN2F, z: ArrayLikeN2F) -> xr.Dataset:
    #     """Get fields at a point relative to monitor center in cartesian coordinates.

    #     Parameters
    #     ----------
    #     x : Union[float, Tuple[float, ...], np.ndarray]
    #         (micron) x positions relative to the local origin.
    #     y : Union[float, Tuple[float, ...], np.ndarray]
    #         (micron) y positions relative to the local origin.
    #     z : Union[float, Tuple[float, ...], np.ndarray]
    #         (micron) z positions relative to the local origin.

    #     Returns
    #     -------
    #     xarray.Dataset
    #         xarray dataset containing (Ex, Ey, Ez), (Hx, Hy, Hz) in cartesian coordinates.
    #     """

    #     x, y, z = [np.atleast_1d(x), np.atleast_1d(y), np.atleast_1d(z)]

    #     Ex_data = np.zeros((len(x), len(y), len(z)), dtype=complex)
    #     Ey_data = np.zeros_like(Ex_data)
    #     Ez_data = np.zeros_like(Ex_data)

    #     Hx_data = np.zeros_like(Ex_data)
    #     Hy_data = np.zeros_like(Ex_data)
    #     Hz_data = np.zeros_like(Ex_data)

    #     for i in track(np.arange(len(x)), description="Computing far fields"):
    #         _x = x[i]
    #         for j in np.arange(len(y)):
    #             _y = y[j]
    #             for k in np.arange(len(z)):
    #                 _z = z[k]

    #                 r, theta, phi = self._car_2_sph(_x, _y, _z)
    #                 _field_data = self.fields_spherical(r, theta, phi)

    #                 Er, Et, Ep = [_field_data[comp].values \
    #                     for comp in ["E_r", "E_theta", "E_phi"]]
    #                 Hr, Ht, Hp = [_field_data[comp].values \
    #                     for comp in ["H_r", "H_theta", "H_phi"]]

    #                 Ex_data[i, j, k], Ey_data[i, j, k], Ez_data[i, j, k] = self._sph_2_car_field(
    #                     Er, Et, Ep, theta, phi
    #                 )
    #                 Hx_data[i, j, k], Hy_data[i, j, k], Hz_data[i, j, k] = self._sph_2_car_field(
    #                     Hr, Ht, Hp, theta, phi
    #                 )

    #     dims = ("x", "y", "z")
    #     coords = {"x": np.array(x), "y": np.array(y), "z": np.array(z)}

    #     Ex = xr.DataArray(np.array(Ex_data), coords=coords, dims=dims)
    #     Ey = xr.DataArray(np.array(Ey_data), coords=coords, dims=dims)
    #     Ez = xr.DataArray(np.array(Ez_data), coords=coords, dims=dims)

    #     Hx = xr.DataArray(np.array(Hx_data), coords=coords, dims=dims)
    #     Hy = xr.DataArray(np.array(Hy_data), coords=coords, dims=dims)
    #     Hz = xr.DataArray(np.array(Hz_data), coords=coords, dims=dims)

    #     return xr.Dataset({"Ex": Ex, "Ey": Ey, "Ez": Ez, "Hx": Hx, "Hy": Hy, "Hz": Hz})

    # def power_cartesian(self, x: ArrayLikeN2F, y: ArrayLikeN2F, z: ArrayLikeN2F) -> xr.DataArray:
    #     """Get power scattered to a point relative to the local origin in cartesian coordinates.

    #     Parameters
    #     ----------
    #     x : Union[float, Tuple[float, ...], np.ndarray]
    #         (micron) x distances relative to the local origin.
    #     y : Union[float, Tuple[float, ...], np.ndarray]
    #         (micron) y distances relative to the local origin.
    #     z : Union[float, Tuple[float, ...], np.ndarray]
    #         (micron) z distances relative to the local origin.

    #     Returns
    #     -------
    #     power : xarray.DataArray
    #         Power at points relative to the local origin.
    #     """

    #     x, y, z = [np.atleast_1d(x), np.atleast_1d(y), np.atleast_1d(z)]

    #     power_data = np.zeros((len(x), len(y), len(z)))

    #     for i in track(np.arange(len(x)), description="Computing far field power"):
    #         _x = x[i]
    #         for j in np.arange(len(y)):
    #             _y = y[j]
    #             for k in np.arange(len(z)):
    #                 _z = z[k]

    #                 r, theta, phi = self._car_2_sph(_x, _y, _z)
    #                 power_data[i, j, k] = self.power_spherical(r, theta, phi).values

    #     dims = ("x", "y", "z")
    #     coords = {"x": x, "y": y, "z": z}

    #     return xr.DataArray(data=power_data, coords=coords, dims=dims)

    # @staticmethod
    # def _car_2_sph(x, y, z):
    #     """
    #     Parameters
    #     ----------
    #     x : float
    #         x coordinate.
    #     y : float
    #         y coordinate.
    #     z : float
    #         z coordinate.

    #     Returns
    #     -------
    #     tuple
    #         r, theta, and phi in spherical coordinates.
    #     """
    #     r = np.sqrt(x**2 + y**2 + z**2)
    #     theta = np.arccos(z / r)
    #     phi = np.arctan2(y, x)
    #     return r, theta, phi

    # @staticmethod
    # def _sph_2_car(r, theta, phi):
    #     """coordinates only

    #     Parameters
    #     ----------
    #     r : float
    #         radius.
    #     theta : float
    #         polar angle (rad) downward from x=y=0 line.
    #     phi : float
    #         azimuthal (rad) angle from y=z=0 line.

    #     Returns
    #     -------
    #     tuple
    #         x, y, and z in cartesian coordinates.
    #     """
    #     r_sin_theta = r * np.sin(theta)
    #     x = r_sin_theta * np.cos(phi)
    #     y = r_sin_theta * np.sin(phi)
    #     z = r * np.cos(theta)
    #     return x, y, z

    # @staticmethod
    # def _sph_2_car_field(Ar, Atheta, Aphi, theta, phi):
    #     """Convert vector field components in spherical coordinates to cartesian.

    #     Parameters
    #     ----------
    #     Ar : float
    #         radial component of vector A.
    #     Atheta : float
    #         polar angle component of vector A.
    #     Aphi : float
    #         azimuthal angle component of vector A.
    #     theta : float
    #         polar angle (rad) of location of A.
    #     phi : float
    #         azimuthal angle (rad) of location of A.

    #     Returns
    #     -------
    #     tuple
    #         x, y, and z components of A in cartesian coordinates.
    #     """
    #     sin_theta = np.sin(theta)
    #     cos_theta = np.cos(theta)
    #     sin_phi = np.sin(phi)
    #     cos_phi = np.cos(phi)
    #     Ax = Ar * sin_theta * cos_phi + Atheta * cos_theta * cos_phi - Aphi * sin_phi
    #     Ay = Ar * sin_theta * sin_phi + Atheta * cos_theta * sin_phi + Aphi * cos_phi
    #     Az = Ar * cos_theta - Atheta * sin_theta
    #     return Ax, Ay, Az
