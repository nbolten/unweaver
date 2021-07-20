"""Reusable, sqlite-backed edge containers"""
# For annotating returning class from within class method
from __future__ import annotations
from collections.abc import Mapping
from typing import Any, Dict, Iterator, MutableMapping, Union

from unweaver.exceptions import ImmutableGraphError
from unweaver.graph_types import EdgeData
from unweaver.network_adapters import GeoPackageNetwork


FlexibleMapping = Union[MutableMapping, Dict]


class EdgeView(Mapping):
    """Read-only edge attributes that can be updated from the GeoPackage
    (SQLite) database or initialized with kwargs (kwargs will be stored
    in-memory).

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
        self.ddict: FlexibleMapping = dict()
        if kwargs:
            self.ddict.update(kwargs)
        else:
            self.sync_from_db()

    def sync_from_db(self) -> None:
        self.ddict = dict(self.network.edges.get_edge(self.u, self.v))

    def sync_to_db(self) -> None:
        raise ImmutableGraphError(
            "Attempt to write edge attributes to immutable graph."
        )

    @classmethod
    def from_db(cls, network: GeoPackageNetwork, u: str, v: str) -> EdgeView:
        return cls(
            _network=network, _u=u, _v=v, **network.edges.get_edge(u, v)
        )

    def __getitem__(self, key: str) -> EdgeData:
        return self.ddict[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.ddict)

    def __len__(self) -> int:
        return len(self.ddict)

    # Revisit the necessity of this - satisfy AbstractSet another way?
    def __hash__(self) -> int:
        return hash((self.u, self.v))
