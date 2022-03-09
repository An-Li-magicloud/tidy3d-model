# pylint:disable=too-many-arguments
"""Defines Geometric objects with Medium properties."""
import pydantic

from .base import Tidy3dBaseModel
from .validators import validate_name_str
from .geometry import GeometryType, Box  # pylint: disable=unused-import
from .medium import MediumType, Medium  # pylint: disable=unused-import
from .types import Ax, PlotlyFig
from .viz import add_ax_if_none, equal_aspect, add_fig_if_none


class Structure(Tidy3dBaseModel):
    """Defines a physical object that interacts with the electromagnetic fields.
    A :class:`Structure` is a combination of a material property (:class:`AbstractMedium`)
    and a :class:`Geometry`.

    Example
    -------
    >>> box = Box(center=(0,0,1), size=(2, 2, 2))
    >>> glass = Medium(permittivity=3.9)
    >>> struct = Structure(geometry=box, medium=glass, name='glass_box')
    """

    geometry: GeometryType = pydantic.Field(
        ..., title="Geometry", description="Defines geometric properties of the structure."
    )

    medium: MediumType = pydantic.Field(
        ...,
        title="Medium",
        description="Defines the electromagnetic properties of the structure's medium.",
    )

    name: str = pydantic.Field(None, title="Name", description="Optional name for the structure.")

    _name_validator = validate_name_str()

    @property
    def plot_params(self):
        """Uses self.geometry plot parameters."""
        return self.geometry.plot_params

    @equal_aspect
    @add_ax_if_none
    def plot(self, x: float = None, y: float = None, z: float = None, ax: Ax = None) -> Ax:
        """Plot structure's geometric cross section at single (x,y,z) coordinate.

        Parameters
        ----------
        x : float = None
            Position of plane in x direction, only one of x,y,z can be specified to define plane.
        y : float = None
            Position of plane in y direction, only one of x,y,z can be specified to define plane.
        z : float = None
            Position of plane in z direction, only one of x,y,z can be specified to define plane.
        ax : matplotlib.axes._subplots.Axes = None
            Matplotlib axes to plot on, if not specified, one is created.

        Returns
        -------
        matplotlib.axes._subplots.Axes
            The supplied or created matplotlib axes.
        """
        return self.geometry.plot(x=x, y=y, z=z, ax=ax)

    @add_fig_if_none
    def plotly(
        self,
        x: float = None,
        y: float = None,
        z: float = None,
        fig: PlotlyFig = None,
        row: int = None,
        col: int = None,
    ) -> PlotlyFig:
        """Use plotly to plot structure's geometric cross section at single (x,y,z) coordinate."""
        return self.geometry.plotly(x=x, y=y, z=z, fig=fig, row=row, col=col)
