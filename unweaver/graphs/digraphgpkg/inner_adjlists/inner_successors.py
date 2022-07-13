"""GeoPackage adapter for mutable networkx successor mapping."""
from collections import MutableMapping
from typing import AbstractSet, Tuple

from ..edges import Edge
from .inner_successors_view import InnerSuccessorsView


class InnerSuccessors(InnerSuccessorsView, MutableMapping):
    edge_factory = Edge

    def __setitem__(self, key: str, ddict: dict) -> None:
        self.network.edges.update_edge(self.n, key, ddict)

    def __delitem__(self, key: str) -> None:
        self.network.edges.delete(self.n, key)

    def items(self) -> AbstractSet[Tuple[str, Edge]]:
        # This method is overridden to avoid two round trips to the database.
        return {
            (v, Edge(self.network, self.n, v))
            for v, row in self.iterator(self.n)
        }
