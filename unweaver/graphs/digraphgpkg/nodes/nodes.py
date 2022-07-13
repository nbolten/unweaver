"""Reusable GeoPackage-backed Node container(s)."""
from collections.abc import MutableMapping

from .node import Node
from .nodes_view import NodesView


class Nodes(NodesView, MutableMapping):
    """A mapping from node IDs to nodes. Used by NetworkX classes to iterate
    over and insert nodes.

    :param _network: Underlying graph container with the same signature as
                     unweaver.network_adapters.GeoPackageNetwork.
    :type _network: unweaver.network_adapters.GeoPackageNetwork

    """

    def __getitem__(self, key: str) -> Node:
        return Node(key, _network=self.network)

    def __setitem__(self, key: str, ddict: dict) -> None:
        if key in self:
            self.network.nodes.update_node(key, ddict)
        else:
            self.network.nodes.insert(key, ddict)

    def __delitem__(self, key: str) -> None:
        if key in self:
            self.network.nodes.delete(key)
        else:
            raise KeyError(key)
