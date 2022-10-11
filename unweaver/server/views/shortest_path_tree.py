from typing import Any, Iterable, Mapping, Tuple, Union

from flask import g
from marshmallow import Schema, fields
from shapely.geometry import mapping  # type: ignore

from unweaver.candidates import waypoint_candidates, choose_candidate
from unweaver.constants import DWITHIN
from unweaver.geojson import Feature, Point, makePointFeature
from unweaver.graphs import AugmentedDiGraphGPKGView
from unweaver.graph_types import CostFunction, EdgeData
from unweaver.shortest_paths.shortest_path_tree import (
    shortest_path_tree,
    ReachedNode,
    ReachedNodes,
)

from .base_view import BaseView


class ShortestPathTreeSchema(Schema):
    lon = fields.Float(required=True)
    lat = fields.Float(required=True)
    max_cost = fields.Float(required=True)


class ShortestPathTreeView(BaseView):
    view_name = "shortest_path_tree"
    schema = ShortestPathTreeSchema

    def run_analysis(
        self, arguments: Mapping, cost_function: CostFunction
    ) -> Union[
        Tuple[str],
        Tuple[
            str,
            AugmentedDiGraphGPKGView,
            Feature[Point],
            ReachedNodes,
            Any,
            Iterable[EdgeData],
        ],
    ]:
        lon = arguments["lon"]
        lat = arguments["lat"]
        max_cost = arguments["max_cost"]

        candidates = waypoint_candidates(g.G, lon, lat, 4, dwithin=DWITHIN)
        if candidates is None:
            # TODO: return too-far-away result
            # TODO: normalize return type to be mapping with optional keys
            return ("InvalidWaypoint",)
        candidate = choose_candidate(g.G, candidates, "origin", cost_function)
        if candidate is None:
            # TODO: return no-suitable-start-candidates result
            return ("InvalidWaypoint",)

        G_aug = AugmentedDiGraphGPKGView.prepare_augmented(g.G, candidate)
        if self.profile.get("precalculate", False):
            reached_nodes, paths, edges = shortest_path_tree(
                G_aug,
                candidate.n,
                cost_function,
                max_cost,
                self.precalculated_cost_function,
            )
        else:
            reached_nodes, paths, edges = shortest_path_tree(
                G_aug, candidate.n, cost_function, max_cost, cost_function
            )

        geom_key = g.G.network.nodes.geom_column
        nodes: ReachedNodes = {}
        for node_id, reached_node in reached_nodes.items():
            node_attr = G_aug.nodes[node_id]
            # TODO: figure out why we're retrieving attrs from G_aug here?
            nodes[node_id] = ReachedNode(
                key=node_id, geom=node_attr[geom_key], cost=reached_node.cost
            )
        origin = makePointFeature(*mapping(candidate.geometry)["coordinates"])

        return ("Ok", G_aug, origin, nodes, paths, edges)
