from unweaver.graphs.augmented import prepare_augmented
from unweaver.graph import waypoint_candidates

from .constants import BOOKSTORE_POINT


def test_augmented(built_G):
    # TODO: test more functionality. What should an augmented graph object be
    # able to do?

    # TODO: include multiple candidate types: mid-edge and on-node
    candidates = waypoint_candidates(
        built_G, BOOKSTORE_POINT[0], BOOKSTORE_POINT[1], 1
    )
    candidate = next(candidates)

    # TODO: Test output
    prepare_augmented(built_G, candidate)
