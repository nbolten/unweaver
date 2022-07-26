# Command to test: poetry run pytest tests/test_polygon.py
from shapely.geometry import Polygon
from unweaver.databases.geopackage.building_table import BuildingTable
from .constants import EXAMPLE_POLYGON, BUILD_PATH

def test_building(built_G):
    pass