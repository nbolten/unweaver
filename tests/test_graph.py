from shapely.geometry import LineString

from entwiner.utils import haversine
from unweaver.graph import (
    is_end_node,
    is_start_node,
    new_edge,
    reverse_edge,
    waypoint_candidates,
)

from .constants import BOOKSTORE_POINT


def test_waypoint_candidates(built_G):
    # TODO: test more variations to arguments
    candidates = waypoint_candidates(
        built_G,
        BOOKSTORE_POINT[0],
        BOOKSTORE_POINT[1],
        4,
        is_destination=False,
        dwithin=10,
        invert=("incline",),
        flip=None,
    )
    candidates = list(candidates)
    assert len(candidates) > 0

    candidate = candidates[0]

    # is a pseudo-edge
    assert candidate.edge1[0] == -1
    # expect exactly this edge - fid 50
    assert candidate.edge1[2]["fid"] == 50
    # Double check that it's a sidewalk
    assert candidate.edge1[2]["footway"] == "sidewalk"
    edge1_len = haversine(candidate.edge1[2]["geom"]["coordinates"])
    # There may be slight variation over time in distance calculations, so
    # check if in the right ballpark
    assert (edge1_len - 63.5) < 0.1

    # is a pseudo-edge
    assert candidate.edge2[0] == -1
    # expect exactly this edge - fid 50
    assert candidate.edge2[2]["fid"] == 50
    # Double check that it's a sidewalk
    assert candidate.edge2[2]["footway"] == "sidewalk"
    edge2_len = haversine(candidate.edge2[2]["geom"]["coordinates"])
    # There may be slight variation over time in distance calculations, so
    # check if in the right ballpark
    assert (edge2_len - 19.6) < 0.1

    # Made-up node ID (node will be injected into augmented graph)
    assert candidate.n == -1

    assert candidate.geometry.x == -122.313108
    assert candidate.geometry.y == 47.661011


def test_reverse_edge(built_G):
    example_edge = {
        "geom": {"type": "LineString", "coordinates": [[0, 1], [1, 0],]},
        "width": 0.4,
        "incline": 0.1,
    }

    # TODO: test more inputs, including 'flip' argument
    reverse_edge(built_G, example_edge, invert=("incline",), flip=None)

    # Verify that geometry flips
    # Mutated `example_edge` in-place
    assert example_edge["geom"]["coordinates"][0][0] == 1
    assert example_edge["geom"]["coordinates"][0][1] == 0
    assert example_edge["geom"]["coordinates"][1][0] == 0
    assert example_edge["geom"]["coordinates"][1][1] == 1

    assert example_edge["width"] == 0.4

    assert example_edge["incline"] == -0.1


def test_is_start_node():
    assert is_start_node(0.0)
    assert not is_start_node(0.1)


def test_is_end_node():
    linestring = LineString([[0, 0], [0, 1],])

    assert is_end_node(1, linestring)
    assert is_end_node(1 - 1e-13, linestring)
    assert not is_end_node(1 - 0.1, linestring)


def test_new_edge(built_G):
    geom = LineString(((2, 0), (1, 0),))

    d = {
        "geom": {"type": "LineString", "coordinates": [[3, 0], [1, 0],]},
        "width": 0.4,
        "incline": 0.1,
        "length": 2,
    }

    d2 = new_edge(built_G, geom, d)

    assert d2["width"] == 0.4
    assert d2["incline"] == 0.1
    assert d2["length"] == 1
