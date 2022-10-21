from typing import Dict, List, Tuple, Union

from flask import g
from marshmallow import Schema, fields


from unweaver.graph import ProjectedNode
from unweaver.graph_types import CostFunction, EdgeData
from unweaver.geojson import Feature, Point, makePointFeature
from unweaver.graphs import DiGraphGPKG
from unweaver.shortest_paths.shortest_path import (
    shortest_path_multi,
    waypoint_nodes,
    NoPathError,
)
from .base_view import BaseView


class ShortestPathSchema(Schema):
    lon1 = fields.Float(required=True)
    lat1 = fields.Float(required=True)
    lon2 = fields.Float(required=True)
    lat2 = fields.Float(required=True)


class ShortestPathView(BaseView):
    view_name = "shortest_path"
    schema = ShortestPathSchema

    def run_analysis(
        self, arguments: Dict, cost_function: CostFunction
    ) -> Union[
        Tuple[str],
        Tuple[
            str,
            DiGraphGPKG,
            Feature[Point],
            Feature[Point],
            float,
            List[str],
            List[EdgeData],
        ],
    ]:
        lon1 = arguments["lon1"]
        lat1 = arguments["lat1"]
        lon2 = arguments["lon2"]
        lat2 = arguments["lat2"]

        waypoints = [
            makePointFeature(lon1, lat1),
            makePointFeature(lon2, lat2),
        ]
        nodes = waypoint_nodes(g.G, waypoints, cost_function)

        # NOTE: Have to create new variable for mypy to notice that a None
        # check has been done...
        checked_nodes: List[Union[str, ProjectedNode]] = []
        for node in nodes:
            if node is None:
                return ("InvalidWaypoint",)
            checked_nodes.append(node)

        cost: float
        path: List[str]
        edges: List[EdgeData]

        if (
            self.profile.get("precalculate", False)
            and self.precalculated_cost_function is not None
        ):
            cost_fun = self.precalculated_cost_function
        else:
            cost_fun = cost_function

        try:
            cost, path, edges = shortest_path_multi(
                g.G, checked_nodes, cost_fun
            )
        except NoPathError:
            return ("NoPath",)

        origin = makePointFeature(lon1, lat1)
        destination = makePointFeature(lon2, lat2)

        return ("Ok", g.G, origin, destination, cost, path, edges)
