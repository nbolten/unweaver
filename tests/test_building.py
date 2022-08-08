# Command to test: poetry run pytest tests/test_building.py
from unweaver.databases.geopackage.geopackage import GeoPackage
from unweaver.databases.geopackage.geom_types import GeoPackageGeoms
from .constants import EXAMPLE_POLYGON
from shapely.geometry import shape

"""
Notes:
- WKT for point: POINT (1.0 4.0)
- WKB: stored as binary
"""

def test_building():
    gpkg = GeoPackage()
    table = gpkg.add_feature_table("building", GeoPackageGeoms.POLYGON)
    assert table.name == "building" # Making sure table is made
    assert gpkg._is_connected()

    # Writing to database
    polygon = shape(EXAMPLE_POLYGON["geometry"])
    table.write_feature({
        "geom": polygon
    })

    # Retrieve the feature
    assert next(iter(table))["geom"] == EXAMPLE_POLYGON["geometry"]