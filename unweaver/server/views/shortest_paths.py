from typing import Any, Iterable, Mapping, Tuple, Union

from flask import g
from marshmallow import Schema, fields
from shapely.geometry import mapping

from unweaver.geojson import Feature, Point, makePointFeature
from unweaver.graph import CostFunction
from unweaver.graphs.augmented import prepare_augmented, AugmentedDiGraphDBView
from unweaver.constants import DWITHIN
from unweaver.graph import waypoint_candidates, choose_candidate, EdgeData
from unweaver.algorithms.shortest_paths import (
    shortest_paths,
    ReachedNode,
    ReachedNodes,
)

from .base_view import BaseView


class ShortestPathsSchema(Schema):
    lon = fields.Float(required=True)
    lat = fields.Float(required=True)
    max_cost = fields.Float(required=True)


class ShortestPathsView(BaseView):
    view_name = "shortest_paths"
    schema = ShortestPathsSchema

    def run_analysis(
        self, arguments: Mapping, cost_function: CostFunction
    ) -> Union[
        str,
        Tuple[
            str,
            AugmentedDiGraphDBView,
            Feature[Point],
            ReachedNodes,
            Any,
            Iterable[EdgeData],
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
            # TODO: normalize return type to be mapping with optional keys
            return "InvalidWaypoint"
        candidate = choose_candidate(candidates, cost_function)
        if candidate is None:
            # TODO: return no-suitable-start-candidates result
            return "InvalidWaypoint"

        G_aug = prepare_augmented(g.G, candidate)
        reached_nodes, paths, edges = shortest_paths(
            G_aug,
            candidate.n,
            cost_function,
            max_cost,
            self.precalculated_cost_function,
        )

        geom_key = g.G.network.nodes.geom_column
        nodes: ReachedNodes = {}
        for node_id, reached_node in reached_nodes.items():
            node_attr = G_aug.nodes[node_id]
            # TODO: figure out why we're retrieving attrs from G_aug here?
            nodes[node_id] = ReachedNode(
                key=node_id, geom=node_attr[geom_key], cost=reached_node.cost,
            )
        origin = makePointFeature(*mapping(candidate.geometry)["coordinates"])

        return ("Ok", G_aug, origin, nodes, paths, edges)
