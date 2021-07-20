"""GeoPackage adapter for immutable networkx outer predecessors mapping."""
from ..inner_adjlists import InnerPredecessorsView
from .outer_adjlist_view import OuterAdjlistView


class OuterPredecessorsView(OuterAdjlistView):
    inner_adjlist_factory = InnerPredecessorsView
    iterator_str = "successor_nodes"
    size_str = "unique_successors"
