"""Augmented graph: add temporary nodes to a (read-only) DiGraphGPKG view.
"""
from collections.abc import Mapping
from itertools import chain
from functools import partial
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    Optional,
    Set,
)

import networkx as nx

from unweaver.geojson import Point
from unweaver.graph import ProjectedNode
from unweaver.graphs.digraphgpkg import DiGraphGPKGView


# TODO: create a module with single class per file
class AugmentedNodesView(Mapping):
    mapping_attr = "_node"

    def __init__(self, _G: DiGraphGPKGView, _G_overlay: dict):
        self.mapping = getattr(_G, self.mapping_attr)
        self.mapping_overlay = getattr(_G_overlay, self.mapping_attr)

    def __getitem__(self, key: str) -> Dict[Any, Any]:
        if key in self.mapping_overlay:
            return self.mapping_overlay[key]

        if key in self.mapping:
            return self.mapping[key]

        raise KeyError

    def __iter__(self) -> Iterator[str]:
        seen: Set[str] = set([])
        for key in iter(self.mapping_overlay):
            yield key
            seen.add(key)

        for key in iter(self.mapping):
            if key not in seen:
                yield key

    def __len__(self) -> int:
        # FIXME: this is not actually correct if the two graphs share keys.
        return len(self.mapping) + len(self.mapping_overlay)


class AugmentedOuterSuccessorsView(Mapping):
    mapping_attr = "_succ"

    def __init__(self, _G: DiGraphGPKGView, _G_overlay: dict):
        self.mapping = getattr(_G, self.mapping_attr)
        self.mapping_overlay = getattr(_G_overlay, self.mapping_attr)

    # TODO: Improve the type definitions here
    def __getitem__(self, key: str) -> Dict[Any, Any]:
        mapping_adj = tuple(self.mapping.get(key, {}).items())
        mapping_overlay_adj = tuple(self.mapping_overlay.get(key, {}).items())

        if mapping_adj or mapping_overlay_adj:
            return dict(chain(mapping_adj, mapping_overlay_adj))

        raise KeyError

    def __iter__(self) -> Iterator[str]:
        seen = set([])
        for key in iter(self.mapping_overlay):
            yield key
            seen.add(key)

        for key in iter(self.mapping):
            if key not in seen:
                yield key

    def __len__(self) -> int:
        # FIXME: this is not actually correct if the two graphs share keys.
        return len(self.mapping) + len(self.mapping_overlay)


class AugmentedOuterPredecessorsView(AugmentedOuterSuccessorsView):
    mapping_attr = "_pred"


class AugmentedDiGraphGPKGView(nx.DiGraph):
    node_dict_factory: Callable = AugmentedNodesView
    adjlist_outer_dict_factory: Callable = AugmentedOuterSuccessorsView
    # In networkx, inner adjlist is only ever invoked without parameters in
    # order to assign new nodes or edges with no attr. Therefore, its
    # functionality can be accounted for elsewhere: via __getitem__ and
    # __setitem__ on the outer adjacency list.
    adjlist_inner_dict_factory = dict
    edge_attr_dict_factory: Callable = dict

    def __init__(self, G: DiGraphGPKGView, G_overlay: Optional[dict] = None):
        if G_overlay is None:
            G_overlay = {}
        # The factories of nx dict-likes need to be informed of the connection
        setattr(
            self,
            "node_dict_factory",
            partial(self.node_dict_factory, _G=G, _G_overlay=G_overlay),
        )
        setattr(
            self,
            "adjlist_outer_dict_factory",
            partial(
                self.adjlist_outer_dict_factory, _G=G, _G_overlay=G_overlay
            ),
        )
        # Not 'partial' on this?
        setattr(
            self, "adjlist_inner_dict_factory", self.adjlist_inner_dict_factory
        )
        setattr(
            self,
            "edge_attr_dict_factory",
            partial(self.edge_attr_dict_factory, _G=G, _G_overlay=G_overlay),
        )

        self.graph: Dict[Any, Any] = {}
        setattr(self, "_node", self.node_dict_factory())
        self._succ = self._adj = self.adjlist_outer_dict_factory()
        self._pred = AugmentedOuterPredecessorsView(_G=G, _G_overlay=G_overlay)

        self.network = G.network


def prepare_augmented(
    G: DiGraphGPKGView, candidate: ProjectedNode
) -> AugmentedDiGraphGPKGView:
    temp_edges = []
    if candidate.edge1 is not None:
        temp_edges.append(candidate.edge1)
    if candidate.edge2 is not None:
        temp_edges.append(candidate.edge2)

    if temp_edges:
        G_overlay = nx.DiGraph()
        G_overlay.add_edges_from(temp_edges)
        for u, v, d in temp_edges:
            # TODO: 'add_edges_from' should automatically add geometry info to
            #       nodes. This is a workaround for the fact that it doesn't.
            G_overlay.nodes[u][G.network.nodes.geom_column] = Point(
                d[G.network.edges.geom_column]["coordinates"][0]
            )
            G_overlay.nodes[v][G.network.nodes.geom_column] = Point(
                d[G.network.edges.geom_column]["coordinates"][-1]
            )
        G = AugmentedDiGraphGPKGView(G=G, G_overlay=G_overlay)

    return G
