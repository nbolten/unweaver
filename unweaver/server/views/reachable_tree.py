from typing import List, Mapping, Tuple, Union

from flask import g
from marshmallow import Schema, fields
from shapely.geometry import mapping  # type: ignore

from unweaver.candidates import waypoint_candidates, choose_candidate
from unweaver.constants import DWITHIN
from unweaver.geojson import Feature, Point, makePointFeature
from unweaver.graphs import AugmentedDiGraphGPKGView
from unweaver.graph_types import CostFunction, EdgeData
from unweaver.shortest_paths.shortest_path_tree import ReachedNodes
from unweaver.shortest_paths.reachable_tree import reachable_tree

from .base_view import BaseView


class ReachableTreeSchema(Schema):
    lon = fields.Float(required=True)
    lat = fields.Float(required=True)
    max_cost = fields.Float(required=True)


class ReachableTreeView(BaseView):
    view_name = "reachable_tree"
    schema = ReachableTreeSchema

    # TODO: more specific than Mapping
    def run_analysis(
        self, arguments: Mapping, cost_function: CostFunction
    ) -> Union[
        Tuple[str],
        Tuple[
            str,
            AugmentedDiGraphGPKGView,
            Feature[Point],
            ReachedNodes,
            List[EdgeData],
        ],
    ]:
        lon = arguments["lon"]
        lat = arguments["lat"]
        max_cost = arguments["max_cost"]

        candidates = waypoint_candidates(g.G, lon, lat, 4, dwithin=DWITHIN)
        if candidates is None:
            # TODO: return too-far-away result
            return ("InvalidWaypoint",)
        candidate = choose_candidate(g.G, candidates, "origin", cost_function)
        if candidate is None:
            # TODO: return no-suitable-start-candidates result
            return ("InvalidWaypoint",)

        G_aug = AugmentedDiGraphGPKGView.prepare_augmented(g.G, candidate)
        if self.profile.get("precalculate", False):
            nodes, edges = reachable_tree(
                G_aug,
                candidate,
                cost_function,
                max_cost,
                self.precalculated_cost_function,
            )
        else:
            nodes, edges = reachable_tree(
                G_aug, candidate, cost_function, max_cost, cost_function
            )

        origin = makePointFeature(*mapping(candidate.geometry)["coordinates"])

        return ("Ok", G_aug, origin, nodes, edges)
