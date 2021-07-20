"""Reusable, sqlite-backed edge containers"""
from collections.abc import MutableMapping
from typing import Any

from unweaver.network_adapters import GeoPackageNetwork
from .edge_dict import EdgeDict
from .edge_view import EdgeView


class Edge(EdgeView, MutableMapping):
    """Edge attributes that can be updated from the SQLite database or
    initialized with kwargs (kwargs will be stored in-memory).

    :param _network: GeoPackageNetwork used for interacting with underlying
                     graph db.
    :type _network: unweaver.network_adapters.GeoPackageNetwork
    :param _u: first node describing (u, v) edge.
    :type _u: str
    :param _v: second node describing (u, v) edge.
    :type _v: str
    :param kwargs: Dict-like data.
    :type kwargs: dict-like data as keyword arguments.

    """

    def __init__(
        self, _network: GeoPackageNetwork, _u: str, _v: str, **kwargs: Any
    ):
        self.network = _network
        self.u = _u
        self.v = _v
        self.ddict = EdgeDict(_network=_network, _u=_u, _v=_v)
        if kwargs:
            self.ddict.update(kwargs)

    def sync_to_db(self) -> None:
        self.network.edges.update([(self.u, self.v, dict(self.ddict))])

    # TODO: use set of GeoPackage-serializable values instad of Any
    def __setitem__(self, key: str, value: Any) -> None:
        self.ddict[key] = value

    def __delitem__(self, key: str) -> None:
        del self.ddict[key]

    def __hash__(self) -> int:
        return hash((self.u, self.v, self.ddict))
