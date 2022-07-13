"""Reusable, sqlite-backed edge containers"""
from collections.abc import MutableMapping
from typing import Any, Iterator

from unweaver.graph_types import EdgeData
from unweaver.network_adapters import GeoPackageNetwork
from unweaver.exceptions import UninitializedEdgeError


class EdgeDict(MutableMapping):
    """A mutable mapping that always syncs to/from the database edges table."""

    def __init__(
        self, _network: GeoPackageNetwork, _u: str, _v: str,
    ):
        self.network = _network
        self.u = _u
        self.v = _v

    def __getitem__(self, key: str) -> EdgeData:
        return self.network.edges.get_edge(self.u, self.v)[key]

    def __iter__(self) -> Iterator[str]:
        # TODO: speed up by directly asking for keys for this row?
        return iter(self.network.edges.get_edge(self.u, self.v))

    def __len__(self) -> int:
        return len(self.keys())

    # TODO: create set of GPKG-serializable values rather than using Any
    def __setitem__(self, key: str, value: Any) -> None:
        if self.u is not None and self.v is not None:
            self.network.edges.update_edge(self.u, self.v, {key: value})
        else:
            raise UninitializedEdgeError(
                "Attempted to set attrs on uninitialized edge."
            )

    def __delitem__(self, key: str) -> None:
        if self.u is not None and self.v is not None:
            self.network.edges.update_edge(self.u, self.v, {key: None})
        else:
            raise UninitializedEdgeError(
                "Attempted to delete attrs on uninitialized edge."
            )

    def __hash__(self) -> int:
        # TODO: revisit this - does it actually supply information?
        return hash((self.u, self.v))
