"""Augmented graph: add temporary nodes to a view of the `entwiner` database.
"""
from collections.abc import Mapping
from itertools import chain
from functools import partial

import networkx as nx


# TODO: create a module with single class per file
# TODO: merge into `entwiner`?
class AugmentedNodesView(Mapping):
    mapping_attr = "_node"

    def __init__(self, _G, _G_overlay):
        self.mapping = getattr(_G, self.mapping_attr)
        self.mapping_overlay = getattr(_G_overlay, self.mapping_attr)

    def __getitem__(self, key):
        if key in self.mapping_overlay:
            return self.mapping_overlay[key]

        if key in self.mapping:
            return self.mapping[key]

        raise KeyError

    def __iter__(self):
        seen = set([])
        for key in iter(self.mapping_overlay):
            yield key
            seen.push(key)

        for key in iter(self.mapping):
            if key not in seen:
                yield key

    def __len__(self):
        # FIXME: this is not actually correct if the two graphs share keys.
        return len(self.mapping) + len(self.mapping_overlay)


class AugmentedOuterSuccessorsView(Mapping):
    mapping_attr = "_succ"

    def __init__(self, _G, _G_overlay):
        self.mapping = getattr(_G, self.mapping_attr)
        self.mapping_overlay = getattr(_G_overlay, self.mapping_attr)

    def __getitem__(self, key):
        mapping_adj = tuple(self.mapping.get(key, {}).items())
        mapping_overlay_adj = tuple(self.mapping_overlay.get(key, {}).items())

        if mapping_adj or mapping_overlay_adj:
            return dict(chain(mapping_adj, mapping_overlay_adj))

        raise KeyError

    def __iter__(self):
        seen = set([])
        for key in iter(self.mapping_overlay):
            yield key
            seen.push(key)

        for key in iter(self.mapping):
            if key not in seen:
                yield key

    def __len__(self):
        # FIXME: this is not actually correct if the two graphs share keys.
        return len(self.mapping) + len(self.mapping_overlay)


class AugmentedOuterPredecessorsView(AugmentedOuterSuccessorsView):
    mapping_attr = "_pred"


class AugmentedDiGraphDBView(nx.DiGraph):
    node_dict_factory = AugmentedNodesView
    adjlist_outer_dict_factory = AugmentedOuterSuccessorsView
    # In networkx, inner adjlist is only ever invoked without parameters in
    # order to assign new nodes or edges with no attr. Therefore, its
    # functionality can be accounted for elsewhere: via __getitem__ and
    # __setitem__ on the outer adjacency list.
    adjlist_inner_dict_factory = dict
    edge_attr_dict_factory = dict

    def __init__(self, G=None, G_overlay=None):
        # The factories of nx dict-likes need to be informed of the connection
        self.node_dict_factory = partial(
            self.node_dict_factory, _G=G, _G_overlay=G_overlay
        )
        self.adjlist_outer_dict_factory = partial(
            self.adjlist_outer_dict_factory, _G=G, _G_overlay=G_overlay
        )
        self.adjlist_inner_dict_factory = self.adjlist_inner_dict_factory
        self.edge_attr_dict_factory = partial(
            self.edge_attr_dict_factory, _G=G, _G_overlay=G_overlay
        )

        # FIXME: should use a persistent table/container for .graph as well.
        self.graph = {}
        self._node = self.node_dict_factory()
        self._succ = self._adj = self.adjlist_outer_dict_factory()
        self._pred = AugmentedOuterPredecessorsView(_G=G, _G_overlay=G_overlay)

        self.network = G.network


def prepare_augmented(G, candidate):
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
            G_overlay.nodes[u][G.network.nodes.geom_column] = {
                "type": "Point",
                "coordinates": list(
                    d[G.network.edges.geom_column]["coordinates"][0]
                ),
            }
            G_overlay.nodes[v][G.network.nodes.geom_column] = {
                "type": "Point",
                "coordinates": list(
                    d[G.network.edges.geom_column]["coordinates"][-1]
                ),
            }
        G = AugmentedDiGraphDBView(G=G, G_overlay=G_overlay)

    return G
