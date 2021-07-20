"""GeoPackage adapter for mutable networkx predecessor mapping."""
from collections.abc import MutableMapping
from typing import AbstractSet, Tuple

from ..edges import Edge
from .inner_predecessors_view import InnerPredecessorsView


class InnerPredecessors(InnerPredecessorsView, MutableMapping):
    edge_factory = Edge

    def __setitem__(self, key: str, ddict: dict) -> None:
        self.network.edges.update([(key, self.n, ddict)])

    # def __delitem__(self, key: str) -> None:
    #     self.network.delete_edges((key, self.n))

    def items(self) -> AbstractSet[Tuple[str, Edge]]:
        # This method is overridden to avoid two round trips to the database.
        return {
            (u, self.edge_factory(_network=self.network, _u=u, _v=self.n))
            for u, row in self.iterator(self.n)
        }
