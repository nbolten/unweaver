"""Reusable GeoPackage-backed Building container(s)."""
from collections.abc import MutableMapping
from typing import Any

from unweaver.network_adapters import GeoPackageNetwork
from .building_view import BuildingView

class Building(BuildingView, MutableMapping):
    """Retrieves mutable building attributes from table, but does not allow assignment.

    :param b: Building ID.
    :type b: str
    :param _network: Underlying graph container with the same signature as
                     unweaver.network_adapters.GeoPackageNetwork.
    :type _network: unweaver.network_adapters.GeoPackageNetwork

    """

    def __init__(
        self, _network: GeoPackageNetwork, _b: str
    ):
        self.network = _network
        self.b = _b

    def __setitem__(self, key: str, value: Any) -> None:
        self.network.buildings.update_building(self.b, {key: value})

    def __delitem__(self, key: str) -> None:
        if key in self:
            self.network.buildings.update_building(self.b, {key: None})
        else:
            raise KeyError(key)