from unweaver.algorithms.shortest_path import route_legs

from ..constants import cost_fun


def test_route_legs(built_G, test_waypoint_legs):
    # TODO: test output
    node = "-122.313008, 47.6611849"
    cost, path, route = route_legs(built_G, test_waypoint_legs, cost_fun)
