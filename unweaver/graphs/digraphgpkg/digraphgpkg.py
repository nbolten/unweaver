"""Dict-like interface(s) for graphs."""
# importing annotations so that DiGraphGPKG.create_graph can have type hint for
# its own return value (returns DiGraphGPKG)
from __future__ import annotations
import os
from typing import Any, Iterable, Optional

from click._termui_impl import ProgressBar

from unweaver.exceptions import UnderspecifiedGraphError
from unweaver.graph_types import EdgeTuple
from unweaver.network_adapters import GeoPackageNetwork
from .edges import Edge
from .nodes import Nodes
from .outer_adjlists import OuterSuccessors
from .digraphgpkg_view import DiGraphGPKGView


class DiGraphGPKG(DiGraphGPKGView):
    """Mutable directed graph backed by a GeoPackage. An extension of
    unweaver.graphs.DiGraphGPKGView.

    :param path: An optional path to database file (or :memory:-type string).
    :param network: An optional path to a custom GeoPackageNetwork instance.
    :param **kwargs: Keyword arguments compatible with networkx.DiGraph.

    """

    node_dict_factory = Nodes
    adjlist_outer_dict_factory = OuterSuccessors
    # TODO: consider creating a read-only Mapping in the case of immutable
    #       graphs.
    adjlist_inner_dict_factory = dict
    edge_attr_dict_factory = Edge

    def __init__(
        self,
        path: Optional[str] = None,
        network: Optional[GeoPackageNetwork] = None,
        **kwargs: Any
    ):
        # TODO: Consider adding database file existence checker rather than
        #       always checking on initialization?
        if network is None:
            # FIXME: should path be allowed to be None?
            if path is None:
                raise UnderspecifiedGraphError()
            else:
                if not os.path.exists(path):
                    raise UnderspecifiedGraphError(
                        "DB file does not exist. Consider using "
                        "DiGraphGPKG.create_graph"
                    )

                network = GeoPackageNetwork(path)

        super().__init__(path=path, network=network, **kwargs)
        self.mutable = True

    @classmethod
    def create_graph(cls, path: str = None, **kwargs: Any) -> DiGraphGPKG:
        """Create a new DiGraphGPKG (.gpkg) at a given path.

        :param path: The path of the new GeoPackage (.gpkg).
        :param **kwargs: Any other keyword arguments to pass to the new
        DiGraphGPKG instance.
        :returns: A new DiGraphGPKG instance.

        """
        network = GeoPackageNetwork(path)
        return DiGraphGPKG(network=network, **kwargs)

    def add_edges_from(
        self,
        ebunch: Iterable[EdgeTuple],
        _batch_size: int = 1000,
        counter: Optional[ProgressBar] = None,
        **attr: Any
    ) -> None:
        """Equivalent to add_edges_from in networkx but with batched SQL writes.

        :param ebunch: edge bunch, identical to nx ebunch_to_add.
        :param _batch_size: Number of rows to commit to the database at a time.
        :param **attr: Default attributes, identical to nx attr.

        """
        if _batch_size < 2:
            # User has entered invalid number (negative, zero) or 1. Use
            # default behavior.
            super().add_edges_from(self, ebunch, **attr)
            return

        # TODO: length check on each edge
        features = (
            {"_u": edge[0], "_v": edge[1], **edge[2]} for edge in ebunch
        )
        self.network.edges.write_features(
            features, batch_size=_batch_size, counter=counter
        )

    def update_edges(self, ebunch: Iterable[EdgeTuple]) -> None:
        """Update edges as a batch.

        :param ebunch: Any iterable of edge tuples (u, v, d).

        """
        # FIXME: this doesn't actually work. Implement update / upsert
        #        logic for GeoPackage feature tables, then use that.
        self.network.edges.update_edges(ebunch)
