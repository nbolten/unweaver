"""Reusable GeoPackage-backed Node container(s)."""
from collections.abc import Mapping
from typing import Iterator

from unweaver.exceptions import BuildingNotFound
from unweaver.network_adapters import GeoPackageNetwork


class BuildingView(Mapping):
    """Retrieves building attributes from table, but does not allow assignment.

    :param _network: Underlying graph container with the same signature as
                     unweaver.network_adapters.GeoPackageNetwork.
    :type _network: unweaver.network_adapters.GeoPackageNetwork

    """

    def __init__(
        self, _b: str, _network: GeoPackageNetwork,
    ):
        self.b = _b
        self.network = _network

        try:
            # TODO: store the data!
            self.network.nodes.get_building(_b)
        except BuildingNotFound:
            raise KeyError(f"Building {_b} not found")

    # TODO: consider that .items() requires two round trips - may want to
    #       override
    def __getitem__(self, key: str) -> dict:
        try:
            return self.network.buildings.get_building(self.b)[key]
        except BuildingNotFound:
            raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return iter(self.network.buildings.get_building(self.b).keys())

    def __len__(self) -> int:
        return len(self.network.buildings.get_building(self.b))
