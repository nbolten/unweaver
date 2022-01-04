from dataclasses import dataclass, field
from typing import Generic, List, Literal, TypeVar


# TODO: Use Annotated[List[float], 2] for length-2 list in Python 3.9+
Position = List[float]


@dataclass
class Point:
    coordinates: Position
    type: Literal["Point"] = field(default="Point", init=False)


@dataclass
class LineString:
    coordinates: List[Position]
    type: Literal["LineString"] = field(default="LineString", init=False)


GeometryType = TypeVar("GeometryType", Point, LineString)


@dataclass
class Feature(Generic[GeometryType]):
    geometry: GeometryType
    type: Literal["Feature"] = field(default="Feature", init=False)
    properties: dict = field(default_factory=dict)


def makePointFeature(
    lon: float, lat: float, properties: dict = None
) -> Feature[Point]:
    if properties is None:
        properties = {}
    return Feature(geometry=Point([lon, lat]))


def makeLineStringFeature(
    coordinates: List[Position], properties: dict = None
) -> Feature[LineString]:
    if properties is None:
        properties = {}
    return Feature(geometry=LineString(coordinates))
