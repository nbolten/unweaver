"""GeoPackage adapter for mutable networkx outer predecessors mapping."""
from collections.abc import MutableMapping

from ..inner_adjlists import InnerPredecessors
from .outer_predecessors_view import OuterPredecessorsView


class OuterPredecessors(OuterPredecessorsView, MutableMapping):
    inner_adjlist_factory = InnerPredecessors

    # def __setitem__(self, key: str, ddict: dict) -> None:
    #     self.network.replace_predecessors(
    #         key, ((k, v) for k, v in ddict.items())
    #     )

    # def __delitem__(self, key: str) -> None:
    #     self.network.delete_predecessors(key)
