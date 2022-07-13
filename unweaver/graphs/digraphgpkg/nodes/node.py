"""Reusable GeoPackage-backed Node container(s)."""
from collections.abc import MutableMapping
from typing import Any

from .node_view import NodeView


class Node(NodeView, MutableMapping):
    """Retrieves mutable node attributes from table, but does not allow
    assignment.

    :param n: Node ID.
    :type n: str
    :param _network: Underlying graph container with the same signature as
                     unweaver.network_adapters.GeoPackageNetwork.
    :type _network: unweaver.network_adapters.GeoPackageNetwork

    """

    # TODO: create GeoPackage-serializable value type
    def __setitem__(self, key: str, value: Any) -> None:
        self.network.nodes.update_node(self.n, {key: value})

    def __delitem__(self, key: str) -> None:
        if key in self:
            self.network.nodes.update_node(self.n, {key: None})
        else:
            raise KeyError(key)
