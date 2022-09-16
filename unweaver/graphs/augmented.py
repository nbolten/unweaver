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
    Set,
    Type,
    TypeVar,
)

import networkx as nx  # type: ignore

from unweaver.geojson import Point
from unweaver.graph import ProjectedNode
from unweaver.graphs.digraphgpkg import DiGraphGPKGView


T = TypeVar("T", bound="AugmentedDiGraphGPKGView")


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

    def __init__(self, _G: DiGraphGPKGView, _G_overlay: nx.DiGraph):
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
    """A wrapper over DiGraphGPKGView that allows for overlaying an in-memory
    DiGraph but with a seamless interface. When querying the graph, such as
    asking for a particular edge based on a (u, d) pair (G[u][v]), an
    AugmentedDiGraphGPKGView will first attempt to retrieve this edge from
    the in-memory DiGraph, then check the DiGraphGPKGView.

    This wrapper is particularly useful for adding temporary nodes and edges
    for the purposes of running a graph analysis algorithm. For example,
    Unweaver uses AugmentedDiGraphGPKGView when it's necessary to start
    "part-way along" an edge for a shortest-path query using Dijkstra's
    algorithm. There is often no on-graph node near the physical locationfrom
    which someone wants to begin searching for shortest paths, so Unweaver
    creates two new temporary edges starting from the nearest point on the
    nearest edge, connecting them to the on-graph nodes for that edge, and
    creates an AugmentedDiGraphGPKGView using those temporary edges.

    :param G: A DiGraphGPKGView, usually the main graph data.
    :param G_overlay: A dict-of-dict-of-dicts (or networkx.DiGraph) to overlay.

    """

    node_dict_factory: Callable = AugmentedNodesView
    adjlist_outer_dict_factory: Callable = AugmentedOuterSuccessorsView
    # In networkx, inner adjlist is only ever invoked without parameters in
    # order to assign new nodes or edges with no attr. Therefore, its
    # functionality can be accounted for elsewhere: via __getitem__ and
    # __setitem__ on the outer adjacency list.
    adjlist_inner_dict_factory = dict
    edge_attr_dict_factory: Callable = dict

    def __init__(
        self, G: DiGraphGPKGView, G_overlay: nx.DiGraph,
    ):
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

    @classmethod
    def prepare_augmented(
        cls: Type[T], G: DiGraphGPKGView, candidate: ProjectedNode
    ) -> T:
        """Create an AugmentedDiGraphGPKGView based on a DiGraphGPKGView and
        a start point candidatee (a ProjectedNode class instance). This will
        embed an overlay node and two edges.

        :param G: The base DiGraphGPKGView.
        :param candidate: The potential start point candidate.

        """
        temp_edges = []
        if candidate.edges_in:
            for e in candidate.edges_in:
                temp_edges.append(e)
        if candidate.edges_out:
            for e in candidate.edges_out:
                temp_edges.append(e)

        G_overlay = nx.DiGraph()
        if temp_edges:
            G_overlay.add_edges_from(temp_edges)
            for u, v, d in temp_edges:
                # TODO: 'add_edges_from' should automatically add geometry info
                # to nodes. This is a workaround for the fact that it doesn't.
                G_overlay.nodes[u][G.network.nodes.geom_column] = Point(
                    d[G.network.edges.geom_column]["coordinates"][0]
                )
                G_overlay.nodes[v][G.network.nodes.geom_column] = Point(
                    d[G.network.edges.geom_column]["coordinates"][-1]
                )
        G_augmented = AugmentedDiGraphGPKGView(G=G, G_overlay=G_overlay)

        return G_augmented
