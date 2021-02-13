from entwiner import GeoPackageNetwork
from pygtfs import feed


class TransitMixin:
    def add_gtfs(self, path):
        """Read GTFS data source and embed in database."""
        fd = feed.Feed(path)

    def _add_gtfs_stops(self, fd):
        # Add GTFS stops
        # TODO: just extract all fields and coerce to data types via
        # SQLAlchemy.
        # TODO: just use pygtfs table definitions?
        stops = fd.read_table(
            "Stop",
            ("stop_id", "stop_name", "stop_desc", "stop_lon", "stop_lat",),
        )

        self.gpkg.add_feature_table("stops", "POINT", self.srid)
