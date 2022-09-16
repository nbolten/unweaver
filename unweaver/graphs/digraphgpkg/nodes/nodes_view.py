"""Reusable GeoPackage-backed Node container(s)."""
from collections.abc import Mapping
from typing import Iterator

from unweaver.network_adapters import GeoPackageNetwork
from .node_view import NodeView


class NodesView(Mapping):
    """An immutable mapping from node IDs to nodes. Used by NetworkX classes to
    iterate over nodes.

    :param _network: Underlying graph container with the same signature as
                     unweaver.network_adapters.GeoPackageNetwork.

    """

    def __init__(self, _network: GeoPackageNetwork):
        self.network = _network

    def __getitem__(self, key: str) -> NodeView:
        return NodeView(key, _network=self.network)

    def __iter__(self) -> Iterator[str]:
        with self.network.gpkg.connect() as conn:
            query = conn.execute("SELECT _n FROM nodes")
            return (row["_n"] for row in query)

    def __len__(self) -> int:
        with self.network.gpkg.connect() as conn:
            query = conn.execute("SELECT count(*) count FROM nodes")
            return query.fetchone()["count"]
