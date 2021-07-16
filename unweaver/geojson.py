from dataclasses import dataclass, asdict
from typing import Generic, List, Optional, TypeVar


# TODO: Use Annotated[List[float], 2] for length-2 list in Python 3.9+
Position = List[float]


@dataclass
class Point:
    type = "Point"
    coordinates: Position


@dataclass
class LineString:
    type = "LineString"
    coordinates: List[Position]


GeometryType = TypeVar("GeometryType", Point, LineString)


@dataclass
class Feature(Generic[GeometryType]):
    type = "Feature"
    geometry: GeometryType
    properties: Optional[dict] = None

    def as_dict(self) -> dict:
        data = asdict(self)
        return {key: value for key, value in data.items() if value is not None}


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
