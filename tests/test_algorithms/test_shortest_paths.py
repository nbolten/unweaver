from unweaver.algorithms.shortest_paths import shortest_paths

from ..constants import cost_fun, EXAMPLE_NODE


def test_shortest_paths(built_G):
    # TODO: test output # TODO: test augmented graph context version as well
    shortest_paths(built_G, EXAMPLE_NODE, cost_fun, 400)
