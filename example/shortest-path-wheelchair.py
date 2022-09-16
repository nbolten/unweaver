from typing import Iterable

from unweaver.geojson import Feature, Point
from unweaver.graph_types import EdgeTuple
from unweaver.graphs.digraphgpkg import DiGraphGPKGView


def shortest_path(
    status: str,
    G: DiGraphGPKGView = None,
    origin: Feature[Point] = None,
    destination: Feature[Point] = None,
    cost: float = None,
    nodes: Iterable[str] = None,
    edges: Iterable[EdgeTuple] = None,
):
    if status != "Ok":
        return {"status": status}
    else:
        return {"status": status, "path": nodes}
