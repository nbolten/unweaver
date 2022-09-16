from dataclasses import dataclass
from typing import Optional, Tuple

from shapely.geometry import Point  # type: ignore

from unweaver.graph_types import EdgeTuple


# TODO: remove 'n' attribute, it's not used here anyways
@dataclass
class ProjectedNode:
    n: str
    geometry: Point
    edges_in: Optional[Tuple[EdgeTuple, EdgeTuple]] = None
    edges_out: Optional[Tuple[EdgeTuple, EdgeTuple]] = None


def makeNodeID(lon: float, lat: float) -> str:
    return f"{lon}, {lat}"
