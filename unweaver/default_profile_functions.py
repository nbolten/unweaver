from typing import List, Optional

import entwiner

from unweaver.geojson import Feature, Point
from unweaver.graph import EdgeData, CostFunction
from unweaver.algorithms.shortest_paths import Paths, ReachedNodes


def cost_function_generator() -> CostFunction:
    def cost_function(u: str, v: str, d: EdgeData) -> Optional[float]:
        # FIXME: "length" is not guaranteed to exist? Update `entwiner` to
        # calculate a _length attribute for all edges?
        return d.get("length", None)

    return cost_function


def directions(
    status: str,
    G: entwiner.DiGraphDB,
    origin: Feature[Point],
    destination: Feature[Point],
    cost: Optional[float],
    nodes: ReachedNodes,
    edges: List[EdgeData],
) -> dict:
    return {
        "status": status,
        "origin": origin,
        "destination": destination,
        "total_cost": cost,
        "edges": edges,
    }


def shortest_paths(
    status: str,
    G: entwiner.DiGraphDBView,
    origin: Feature[Point],
    nodes: ReachedNodes,
    paths: Paths,
    edges: List[EdgeData],
) -> dict:
    """Return the minimum costs to nodes in the graph."""
    # FIXME: coordinates are derived from node string, should be derived from
    # node metadata (add node coordinates upstream in entwiner).
    return {
        "status": status,
        "origin": origin,
        "paths": list(paths),
        "edges": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": edge.pop(G.network.edges.geom_column),
                    "properties": edge,
                }
                for edge in edges
            ],
        },
        "node_costs": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": n.geom,
                    "properties": {"cost": n.cost},
                }
                for n in nodes.values()
            ],
        },
    }


# TODO: constrain output to be JSON or JSON-like?
def reachable(
    status: str,
    G: entwiner.DiGraphDBView,
    origin: Feature[Point],
    nodes: ReachedNodes,
    edges: List[EdgeData],
) -> dict:
    """Return the total extent of reachable edges."""
    # FIXME: coordinates are derived from node string, should be derived from
    # node metadata (add node coordinates upstream in entwiner).
    unique_edges = []
    seen = set()
    for edge in edges:
        edge_id = (edge["_u"], edge["_v"])

        if edge_id in seen:
            # Skip if we've seen this edge before
            continue
        if (edge_id[1], edge_id[0]) in seen:
            # Skip if we've seen the reverse of this edge before
            continue

        unique_edges.append(edge)
        seen.add(edge_id)

    return {
        "status": status,
        "origin": origin,
        "edges": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": edge.pop(G.network.edges.geom_column),
                    "properties": edge,
                }
                for edge in unique_edges
            ],
        },
        "node_costs": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": node.geom,
                    "properties": {"cost": node.cost},
                }
                for node in nodes.values()
            ],
        },
    }
