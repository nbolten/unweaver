from unweaver.graphs import DiGraphGPKGView
from unweaver.shortest_paths.shortest_path import (
    shortest_path,
    shortest_path_multi,
)

from ..constants import cost_fun


def test_shortest_path_multi(built_G, test_waypoint_nodes):
    # TODO: test output
    cost, path, route = shortest_path_multi(
        built_G, test_waypoint_nodes, cost_fun
    )


def test_shortest_path(built_G, test_waypoint_nodes):
    # TODO: test output
    G = DiGraphGPKGView(network=built_G.network)
    cost, path, route = shortest_path(
        G, test_waypoint_nodes[0], test_waypoint_nodes[1], cost_fun
    )
