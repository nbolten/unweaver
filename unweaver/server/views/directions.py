from typing import Dict, List, Tuple, Union

import entwiner
from flask import g
from marshmallow import Schema, fields

from unweaver.algorithms.shortest_path import (
    route_legs,
    waypoint_legs,
    NoPathError,
)
from unweaver.graph import EdgeData, CostFunction
from unweaver.geojson import Feature, Point, makePointFeature

from .base_view import BaseView


class DirectionsSchema(Schema):
    lon1 = fields.Float(required=True)
    lat1 = fields.Float(required=True)
    lon2 = fields.Float(required=True)
    lat2 = fields.Float(required=True)


class DirectionsView(BaseView):
    view_name = "directions"
    schema = DirectionsSchema

    def run_analysis(
        self, arguments: Dict, cost_function: CostFunction
    ) -> Union[
        Tuple[str],
        Tuple[
            str,
            entwiner.DiGraphDB,
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
        legs = waypoint_legs(g.G, waypoints, cost_function)

        # NOTE: Have to create new variable for mypy to notice that a None
        # check has been done...
        checked_legs = []
        for i, (wp1, wp2) in enumerate(legs):
            if wp1 is None or wp2 is None:
                return ("InvalidWaypoint",)
            checked_legs.append((wp1, wp2))

        cost: float
        path: List[str]
        edges: List[EdgeData]

        if self.precalculated_cost_function is None:
            try:
                cost, path, edges = route_legs(
                    g.G, checked_legs, cost_function
                )
            except NoPathError:
                return ("NoPath",)
        else:
            try:
                cost, path, edges = route_legs(
                    g.G, checked_legs, self.precalculated_cost_function
                )
            except NoPathError:
                return ("NoPath",)

        origin = makePointFeature(lon1, lat1)
        destination = makePointFeature(lon2, lat2)

        return (
            "Ok",
            g.G,
            origin,
            destination,
            cost,
            path,
            edges,
        )
