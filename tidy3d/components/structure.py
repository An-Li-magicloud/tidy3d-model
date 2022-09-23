"""Defines Geometric objects with Medium properties."""
import pydantic

from .base import Tidy3dBaseModel
from .validators import validate_name_str
from .geometry import GeometryType
from .medium import MediumType
from .types import  TYPE_TAG_STR


class Structure(Tidy3dBaseModel):
    """Defines a physical object that interacts with the electromagnetic fields.
    A :class:`Structure` is a combination of a material property (:class:`AbstractMedium`)
    and a :class:`Geometry`.

    Example
    -------
    >>> from tidy3d import Box, Medium
    >>> box = Box(center=(0,0,1), size=(2, 2, 2))
    >>> glass = Medium(permittivity=3.9)
    >>> struct = Structure(geometry=box, medium=glass, name='glass_box')
    """

    geometry: GeometryType = pydantic.Field(
        ...,
        title="Geometry",
        description="Defines geometric properties of the structure.",
        discriminator=TYPE_TAG_STR,
    )

    medium: MediumType = pydantic.Field(
        ...,
        title="Medium",
        description="Defines the electromagnetic properties of the structure's medium.",
        discriminator=TYPE_TAG_STR,
    )

    name: str = pydantic.Field(None, title="Name", description="Optional name for the structure.")

    _name_validator = validate_name_str()

