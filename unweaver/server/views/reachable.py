from typing import List, Mapping, Tuple, Union

from flask import g
from marshmallow import Schema, fields
from shapely.geometry import mapping

from unweaver.geojson import Feature, Point, makePointFeature
from unweaver.graphs.augmented import prepare_augmented, AugmentedDiGraphDBView
from unweaver.constants import DWITHIN
from unweaver.graph import (
    waypoint_candidates,
    choose_candidate,
    EdgeData,
    CostFunction,
)
from unweaver.algorithms.shortest_paths import ReachedNodes
from unweaver.algorithms.reachable import reachable

from .base_view import BaseView


class ReachableSchema(Schema):
    lon = fields.Float(required=True)
    lat = fields.Float(required=True)
    max_cost = fields.Float(required=True)


class ReachableView(BaseView):
    view_name = "reachable"
    schema = ReachableSchema

    # TODO: more specific than Mapping
    def run_analysis(
        self, arguments: Mapping, cost_function: CostFunction
    ) -> Union[
        str,
        Tuple[
            str,
            AugmentedDiGraphDBView,
            Feature[Point],
            ReachedNodes,
            List[EdgeData],
        ],
    ]:
        lon = arguments["lon"]
        lat = arguments["lat"]
        max_cost = arguments["max_cost"]

        candidates = waypoint_candidates(
            g.G, lon, lat, 4, is_destination=False, dwithin=DWITHIN
        )
        if candidates is None:
            # TODO: return too-far-away result
            return "InvalidWaypoint"
        candidate = choose_candidate(candidates, cost_function)
        if candidate is None:
            # TODO: return no-suitable-start-candidates result
            return "InvalidWaypoint"

        G_aug = prepare_augmented(g.G, candidate)
        nodes, edges = reachable(
            G_aug,
            candidate,
            cost_function,
            max_cost,
            self.precalculated_cost_function,
        )
        origin = makePointFeature(*mapping(candidate.geometry)["coordinates"])

        return ("Ok", G_aug, origin, nodes, edges)
