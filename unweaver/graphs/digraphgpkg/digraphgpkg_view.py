"""Dict-like interface(s) for graphs."""
from __future__ import annotations
from typing import Any, Iterable, Optional
import uuid

import networkx as nx  # type: ignore

from unweaver.graph_types import EdgeTuple
from unweaver.network_adapters import GeoPackageNetwork
from .edges import EdgeView
from .nodes import NodesView
from .outer_adjlists import OuterPredecessorsView, OuterSuccessorsView


class DiGraphGPKGView(nx.DiGraph):
    node_dict_factory = NodesView
    adjlist_outer_dict_factory = OuterSuccessorsView
    # In networkx, inner adjlist is only ever invoked without parameters in
    # order to assign new nodes or edges with no attr. Therefore, its
    # functionality can be accounted for elsewhere: via __getitem__ and
    # __setitem__ on the outer adjacency list.
    adjlist_inner_dict_factory = dict
    edge_attr_dict_factory = EdgeView

    def __init__(
        self,
        incoming_graph_data: nx.DiGraph = None,
        path: str = None,
        network: GeoPackageNetwork = None,
        **attr: Any,
    ):
        # Path attr overrides sqlite attr
        if path:
            network = GeoPackageNetwork(path)
        elif network is None:
            raise ValueError("Path or network must be set")

        self.network = network

        # The factories of nx dict-likes need to be informed of the connection
        self.adjlist_inner_dict_factory = self.adjlist_inner_dict_factory

        # FIXME: should use a persistent table/container for .graph as well.
        self.graph = {}
        self._node = self.node_dict_factory(self.network)
        self._succ = self._adj = self.adjlist_outer_dict_factory(self.network)
        self._pred = OuterPredecessorsView(self.network)

        if incoming_graph_data is not None:
            nx.convert.to_networkx_graph(
                incoming_graph_data, create_using=self
            )
        self.graph.update(attr)

        # Set custom flag for read-only graph DBs
        self.mutable = False

    def size(self, weight: Optional[str] = None) -> int:
        if weight is None:
            return len(self.network.edges)
        else:
            return super().size(weight=weight)

    def iter_edges(self) -> Iterable[EdgeTuple]:
        """Roughly equivalent to the .edges interface, but much faster.

        :returns: generator of (u, v, d) similar to .edges, but where d is a
                  dictionary, not an Edge that syncs to database.
        :rtype: tuple generator

        """
        # FIXME: handle case where initializing with ddict data from query.
        # If implemented here (adding **d to the edge factory arguments), it
        # will always attempt to update the database on a per-read basis!
        return (
            (u, v, dict(self.edge_attr_dict_factory(self.network, u, v)))
            for u, v, d in self.network.edges.iter_edges()
        )

    def edges_dwithin(
        self, lon: float, lat: float, distance: float, sort: bool = False
    ) -> Iterable[EdgeTuple]:
        # TODO: document self.network.edges instead?
        return self.network.edges.dwithin_edges(lon, lat, distance, sort=sort)

    def to_in_memory(self) -> DiGraphGPKGView:
        # TODO: make into 'copy' method instead, taking path as a parameter?
        db_id = uuid.uuid4()
        path = f"file:unweaver-{db_id}?mode=memory&cache=shared"
        new_network = self.network.copy(path)
        return self.__class__(network=new_network)
