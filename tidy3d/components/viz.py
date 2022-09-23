# pylint: disable=invalid-name
""" utilities for plotting """
from typing import Any
from functools import wraps


from numpy import array, concatenate, ones
import pydantic as pd

from .base import Tidy3dBaseModel

""" Constants """

# add this around extents of plots
PLOT_BUFFER = 0.3

ARROW_COLOR_MONITOR = "orange"
ARROW_COLOR_SOURCE = "green"
ARROW_COLOR_POLARIZATION = "brown"
ARROW_ALPHA = 0.8


# this times the min of axis height and width gives the arrow length
ARROW_LENGTH_FACTOR = 0.1

# this times ARROW_LENGTH gives width
ARROW_WIDTH_FACTOR = 0.4

# arrow width cannot be larger than this factor times the max of axis height and width
MAX_ARROW_WIDTH_FACTOR = 0.02


""" Decorators """






""" plot parameters """


class PlotParams(Tidy3dBaseModel):
    """Stores plotting parameters / specifications for a given model."""

    alpha: Any = pd.Field(1.0, title="Opacity")
    edgecolor: Any = pd.Field(None, title="Edge Color", alias="ec")
    facecolor: Any = pd.Field(None, title="Face Color", alias="fc")
    fill: bool = pd.Field(True, title="Is Filled")
    hatch: str = pd.Field(None, title="Hatch Style")
    linewidth: pd.NonNegativeFloat = pd.Field(1, title="Line Width", alias="lw")

    def include_kwargs(self, **kwargs) -> "PlotParams":
        """Update the plot params with supplied kwargs."""
        update_dict = {
            key: value
            for key, value in kwargs.items()
            if key not in ("type",) and value is not None and key in self.__fields__
        }
        return self.copy(update=update_dict)

    def to_kwargs(self) -> dict:
        """Export the plot parameters as kwargs dict that can be supplied to plot function."""
        kwarg_dict = self.dict()
        for ignore_key in ("type",):
            kwarg_dict.pop(ignore_key)
        return kwarg_dict


# defaults for different tidy3d objects
plot_params_geometry = PlotParams()
plot_params_structure = PlotParams()
plot_params_source = PlotParams(alpha=0.4, facecolor="limegreen", edgecolor="limegreen", lw=3)
plot_params_monitor = PlotParams(alpha=0.4, facecolor="orange", edgecolor="orange", lw=3)
plot_params_pml = PlotParams(alpha=0.7, facecolor="gray", edgecolor="gray", hatch="x")
plot_params_pec = PlotParams(alpha=1.0, facecolor="gold", edgecolor="black")
plot_params_pmc = PlotParams(alpha=1.0, facecolor="lightsteelblue", edgecolor="black")
plot_params_bloch = PlotParams(alpha=1.0, facecolor="orchid", edgecolor="black")
plot_params_symmetry = PlotParams(edgecolor="gray", facecolor="gray", alpha=0.6)
plot_params_override_structures = PlotParams(linewidth=0.4, edgecolor="black", fill=False)

# stores color of simulation.structures for given index in simulation.medium_map
MEDIUM_CMAP = [
    "#689DBC",
    "#D0698E",
    "#5E6EAD",
    "#C6224E",
    "#BDB3E2",
    "#9EC3E0",
    "#616161",
    "#877EBC",
]


"""=================================================================================================
Descartes modified from https://pypi.org/project/descartes/ for Shapely >= 1.8.0

Copyright Flexcompute 2022

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


class Polygon:
    """Adapt Shapely or GeoJSON/geo_interface polygons to a common interface"""

    def __init__(self, context):
        if isinstance(context, dict):
            self.context = context["coordinates"]
        else:
            self.context = context

    @property
    def exterior(self):
        """Get polygon exterior."""
        return getattr(self.context, "exterior", None) or self.context[0]

    @property
    def interiors(self):
        """Get polygon interiors."""
        value = getattr(self.context, "interiors", None)
        if value is None:
            value = self.context[1:]
        return value

"""End descartes modification
================================================================================================="""
