"""GeoPackage adapter for immutable networkx outer adjascency list mapping."""
from __future__ import annotations
from collections.abc import Mapping
from typing import AbstractSet, Iterator, Tuple, Type, TYPE_CHECKING

from unweaver.network_adapters import GeoPackageNetwork
from ..inner_adjlists import InnerSuccessorsView

if TYPE_CHECKING:
    from ..inner_adjlists import InnerAdjlistView


class OuterAdjlistView(Mapping):
    inner_adjlist_factory = InnerSuccessorsView  # type: Type[InnerAdjlistView]
    iterator_str = "predecessor_nodes"
    size_str = "unique_predecessors"

    def __init__(self, _network: GeoPackageNetwork):
        self.network = _network

        self.inner_adjlist_factory = self.inner_adjlist_factory
        self.iterator = getattr(self.network.edges, self.iterator_str)
        self.size = getattr(self.network.edges, self.size_str)

    def __getitem__(self, key: str) -> InnerAdjlistView:
        return self.inner_adjlist_factory(self.network, key)

    def __iter__(self) -> Iterator[str]:
        # This method is overridden to avoid two round trips to the database.
        return self.iterator()

    def __len__(self) -> int:
        return self.size()

    def items(self) -> AbstractSet[Tuple[str, InnerAdjlistView]]:
        # This method is overridden to avoid two round trips to the database.
        return {
            (n, self.inner_adjlist_factory(_network=self.network, _n=n))
            for n in self.iterator()
        }

    def __contains__(self, key: object) -> bool:
        # This method is overridden because __getitem__ doesn't  initially
        # check for a key's presence.
        # FIXME: should __getitem__ initially check for a key's presence?
        return self.network.has_node(str(key))
