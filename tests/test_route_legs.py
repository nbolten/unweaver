from unweaver.algorithms.shortest_path import route_legs

from .constants import cost_fun


def test_route_legs(built_G, test_waypoint_legs):
    # This route takes 4 seconds or so. Why so slow? Profile.
    cost, path, route = route_legs(built_G, test_waypoint_legs, cost_fun)
