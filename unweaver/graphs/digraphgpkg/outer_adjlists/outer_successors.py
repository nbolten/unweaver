"""GeoPackage adapter for mutable networkx outer successors mapping."""
from ..inner_adjlists import InnerSuccessors
from .outer_successors_view import OuterSuccessorsView


class OuterSuccessors(OuterSuccessorsView):
    inner_adjlist_factory = InnerSuccessors
