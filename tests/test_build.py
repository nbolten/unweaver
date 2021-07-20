import pytest

from unweaver.build.get_layers_paths import get_layers_paths
from unweaver.exceptions import MissingLayersError

from .constants import BUILD_PATH


def test_get_layers_paths():
    paths = get_layers_paths(BUILD_PATH)
    assert paths == ["./tests/data/build/layers/uw.geojson"]
    with pytest.raises(MissingLayersError):
        get_layers_paths("./tests")


def test_build_graph(built_G):
    # TODO: check output
    pass
