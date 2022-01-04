from dataclasses import dataclass, asdict
from typing import ClassVar, Generic, List, Optional, TypeVar


# TODO: Use Annotated[List[float], 2] for length-2 list in Python 3.9+
Position = List[float]


@dataclass
class Point:
    type_: ClassVar[str] = "Point"
    coordinates: Position

    def as_dict(self) -> dict:
        data = asdict(self)
        data["type"] = self.type_
        return data


@dataclass
class LineString:
    type_: ClassVar[str] = "LineString"
    coordinates: List[Position]

    def as_dict(self) -> dict:
        data = asdict(self)
        data["type"] = self.type_
        return data


GeometryType = TypeVar("GeometryType", Point, LineString)


@dataclass
class Feature(Generic[GeometryType]):
    type_: ClassVar[str] = "Feature"
    geometry: GeometryType
    properties: Optional[dict] = None

    def as_dict(self) -> dict:
        data = asdict(self)
        data["type"] = self.type_
        return data


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
