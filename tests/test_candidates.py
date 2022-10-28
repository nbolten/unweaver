from shapely.geometry import LineString, Point

from unweaver.candidates import (
    choose_candidate,
    is_end_node,
    is_start_node,
    new_edge,
    reverse_edge,
    waypoint_candidates,
)
from unweaver.graph import ProjectedNode
from unweaver.utils import haversine

from .constants import BOOKSTORE_POINT, EXAMPLE_NODE


def test_waypoint_candidates(built_G):
    # TODO: test more variations to arguments
    candidates = waypoint_candidates(
        built_G,
        BOOKSTORE_POINT[0],
        BOOKSTORE_POINT[1],
        4,
        dwithin=10,
        invert=("incline",),
        flip=None,
    )
    candidates = list(candidates)
    assert len(candidates) > 0

    candidate = candidates[0]

    assert candidate.edges_out is not None

    # Expect there to be two edges that starts at node "-1"
    assert len(candidate.edges_out) == 2
    # Expect both to have fid 49
    assert all([e[2]["fid"] == 49 for e in candidate.edges_out])
    # Both should be sidewalks
    assert all([e[2]["footway"] == "sidewalk" for e in candidate.edges_out])
    # Get their lengths
    lengths = set(
        [
            round(haversine(e[2]["geom"]["coordinates"]), 2)
            for e in candidate.edges_out
        ]
    )
    assert 19.62 in lengths
    assert 63.49 in lengths

    assert candidate.geometry.x == -122.313108
    assert candidate.geometry.y == 47.661011


def test_reverse_edge(built_G):
    example_edge = {
        "geom": {"type": "LineString", "coordinates": [[0, 1], [1, 0]]},
        "width": 0.4,
        "incline": 0.1,
    }

    # TODO: test more inputs, including 'flip' argument
    reversed_edge = reverse_edge(example_edge, invert=("incline",), flip=None)

    # Verify that geometry flips
    # Mutated `example_edge` in-place
    assert reversed_edge["geom"]["coordinates"][0][0] == 1
    assert reversed_edge["geom"]["coordinates"][0][1] == 0
    assert reversed_edge["geom"]["coordinates"][1][0] == 0
    assert reversed_edge["geom"]["coordinates"][1][1] == 1

    assert reversed_edge["width"] == 0.4

    assert reversed_edge["incline"] == -0.1


def test_is_start_node():
    assert is_start_node(0.0)
    assert not is_start_node(0.1)


def test_is_end_node():
    linestring = LineString([[0, 0], [0, 1]])

    assert is_end_node(1, linestring)
    assert is_end_node(1 - 1e-13, linestring)
    assert not is_end_node(1 - 0.1, linestring)


def test_new_edge(built_G):
    geom = LineString(((2, 0), (1, 0)))

    d = {
        "geom": {"type": "LineString", "coordinates": [[3, 0], [1, 0]]},
        "width": 0.4,
        "incline": 0.1,
        "length": 2,
    }

    d2 = new_edge(built_G, geom, d)

    assert d2["width"] == 0.4
    assert d2["incline"] == 0.1
    assert d2["length"] == 1


def test_choose_candidate(built_G):
    node_candidate = ProjectedNode(
        n=EXAMPLE_NODE, geometry=Point(BOOKSTORE_POINT)
    )
    choose_candidate(built_G, [node_candidate], "origin")
    choose_candidate(built_G, [node_candidate], "destination")
