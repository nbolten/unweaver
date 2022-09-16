from unweaver.candidates import waypoint_candidates
from unweaver.graphs import AugmentedDiGraphGPKGView

from .constants import BOOKSTORE_POINT


def test_augmented(built_G):
    # TODO: test more functionality. What should an augmented graph object be
    # able to do?

    # TODO: include multiple candidate types: mid-edge and on-node
    candidates = waypoint_candidates(
        built_G, BOOKSTORE_POINT[0], BOOKSTORE_POINT[1], 1
    )
    candidate = next(iter(candidates))

    # TODO: Test output
    AugmentedDiGraphGPKGView.prepare_augmented(built_G, candidate)
