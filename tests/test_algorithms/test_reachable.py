from unweaver.algorithms.reachable import reachable
from unweaver.graphs.augmented import prepare_augmented
from unweaver.graph import waypoint_candidates, choose_candidate

from ..constants import cost_fun, BOOKSTORE_POINT


def test_reachable(built_G):
    candidates = waypoint_candidates(
        built_G, BOOKSTORE_POINT[0], BOOKSTORE_POINT[1], 10
    )
    candidate = choose_candidate(candidates, cost_fun)

    # Augmented graph required for reachable to work. Make this consistent and
    # possibly auto-magic
    G_aug = prepare_augmented(built_G, candidate)

    # TODO: test output
    reachable(G_aug, candidate, cost_fun, 400)
