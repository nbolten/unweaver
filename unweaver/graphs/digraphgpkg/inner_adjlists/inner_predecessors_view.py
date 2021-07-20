"""GeoPackage adapter for immutable networkx predecessor mapping."""
from .inner_adjlist_view import InnerAdjlistView


class InnerPredecessorsView(InnerAdjlistView):
    id_iterator_str = "predecessor_nodes"
    iterator_str = "predecessors"
    size_str = "unique_predecessors"
