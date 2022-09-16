from unweaver.shortest_paths.reachable_tree import reachable_tree
from unweaver.candidates import waypoint_candidates, choose_candidate
from unweaver.graphs import AugmentedDiGraphGPKGView

from ..constants import cost_fun, BOOKSTORE_POINT


def test_reachable_tree(built_G):
    candidates = waypoint_candidates(
        built_G, BOOKSTORE_POINT[0], BOOKSTORE_POINT[1], 10
    )
    candidate = choose_candidate(candidates, "origin", cost_fun)

    assert candidate is not None

    # Augmented graph required for reachable to work. Make this consistent and
    # possibly auto-magic
    G_aug = AugmentedDiGraphGPKGView.prepare_augmented(built_G, candidate)

    # TODO: test output
    reachable_tree(G_aug, candidate, cost_fun, 400)
