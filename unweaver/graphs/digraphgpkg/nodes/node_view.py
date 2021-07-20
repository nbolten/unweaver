"""Reusable GeoPackage-backed Node container(s)."""
from collections.abc import Mapping
from typing import Iterator

from unweaver.exceptions import NodeNotFound
from unweaver.network_adapters import GeoPackageNetwork


class NodeView(Mapping):
    """Retrieves node attributes from table, but does not allow assignment.

    :param _network: Underlying graph container with the same signature as
                     unweaver.network_adapters.GeoPackageNetwork.
    :type _network: unweaver.network_adapters.GeoPackageNetwork

    """

    def __init__(
        self, _n: str, _network: GeoPackageNetwork,
    ):
        self.n = _n
        self.network = _network

        try:
            # TODO: store the data!
            self.network.nodes.get_node(_n)
        except NodeNotFound:
            raise KeyError(f"Node {_n} not found")

    # TODO: consider that .items() requires two round trips - may want to
    #       override
    def __getitem__(self, key: str) -> dict:
        try:
            return self.network.nodes.get_node(self.n)[key]
        except NodeNotFound:
            raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return iter(self.network.nodes.get_node(self.n).keys())

    def __len__(self) -> int:
        return len(self.network.nodes.get_node(self.n))
