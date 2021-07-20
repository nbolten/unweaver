import pytest

from unweaver.build.build_graph import build_graph
from unweaver.geojson import makePointFeature
from unweaver.weight import precalculate_weights
from unweaver.algorithms.shortest_path import waypoint_legs

from .constants import cost_fun, BUILD_PATH, CAFE_POINT, BOOKSTORE_POINT


@pytest.fixture(scope="session")
def built_G():
    G = build_graph(
        BUILD_PATH, precision=7, changes_sign=("incline",), counter=None
    )
    return G


@pytest.fixture(scope="session")
def built_G_weighted(built_G):
    precalculate_weights(BUILD_PATH)
    return built_G


@pytest.fixture()
def test_waypoint_legs(built_G):
    origin = makePointFeature(*BOOKSTORE_POINT)
    destination = makePointFeature(*CAFE_POINT)
    # This route takes 4 seconds or so. Why so slow? Profile.
    legs = waypoint_legs(
        built_G, (origin, destination), cost_fun, invert=("incline",)
    )
    # TODO: test output
    return legs
