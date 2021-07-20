"""GeoPackage adapter for networkx inner adjacency list mapping."""
from collections.abc import Mapping
from typing import AbstractSet, Iterator, Tuple

from unweaver.network_adapters import GeoPackageNetwork
from ..edges import EdgeView


class InnerAdjlistView(Mapping):
    edge_factory = EdgeView
    id_iterator_str = "successor_nodes"
    iterator_str = "successors"
    size_str = "unique_successors"

    def __init__(self, _network: GeoPackageNetwork, _n: str):
        self.network = _network
        self.n = _n

        self.id_iterator = getattr(self.network.edges, self.id_iterator_str)
        self.iterator = getattr(self.network.edges, self.iterator_str)
        self.size = getattr(self.network.edges, self.size_str)

    def __getitem__(self, key: str) -> EdgeView:
        return self.edge_factory(self.network, self.n, key)

    def __iter__(self) -> Iterator[str]:
        return iter(self.id_iterator(self.n))

    def __len__(self) -> int:
        return self.size(self.n)

    def items(self) -> AbstractSet[Tuple[str, EdgeView]]:
        # This method is overridden to avoid two round trips to the database.
        return {
            (v, self.edge_factory(self.network, self.n, v, **row))
            for v, row in self.iterator(self.n)
        }
