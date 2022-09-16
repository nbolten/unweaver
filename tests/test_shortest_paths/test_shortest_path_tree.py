from unweaver.shortest_paths.shortest_path_tree import shortest_path_tree

from ..constants import cost_fun, EXAMPLE_NODE


def test_shortest_path_tree(built_G):
    # TODO: test output # TODO: test augmented graph context version as well
    shortest_path_tree(built_G, EXAMPLE_NODE, cost_fun, 400)
