# Imported so that methods can be annotated to return class instance
from __future__ import annotations

import contextlib
import os
import sqlite3
import tempfile
from typing import Any, Dict, Generator

from unweaver.databases.geopackage.feature_table import FeatureTable
from .geom_types import GeoPackageGeoms

GPKG_APPLICATION_ID = 1196444487
GPKG_USER_VERSION = 10200
# FIXME: don't hardcore in-meters SRID, discover an appropriate projection
#        based on data.
# NOTE: this strategy is based around having no function to calculate the
#       distance (meters) between a LineString and a point directly.
TO_SRID = 3740


class GeoPackage:
    VERSION = 0
    EMPTY = 1

    def __init__(self, path: str):
        self.path = path
        self._get_connection()
        self._setup_database()

        self.feature_tables = {}

        # Instantiate FeatureTables that already exist in the db
        with self.connect() as conn:
            query_result = conn.execute(
                "SELECT table_name, srs_id FROM gpkg_contents"
            )
            table_rows = list(query_result)

        for row in table_rows:
            table_name = row["table_name"]

            with self.connect() as conn:
                geom_type_query = conn.execute(
                    """
                    SELECT geometry_type_name
                      FROM gpkg_geometry_columns
                     WHERE table_name = ?
                """,
                    (table_name,),
                )
                geom_type = next(geom_type_query)["geometry_type_name"]

            enum_geom_type = getattr(GeoPackageGeoms, geom_type)

            self.feature_tables[table_name] = FeatureTable(
                self, table_name, enum_geom_type, srid=row["srs_id"]
            )

    def add_feature_table(
        self, name: str, geom_type: GeoPackageGeoms, srid: int = 4326
    ) -> FeatureTable:
        table = FeatureTable(self, name, geom_type, srid=srid)
        table.create_tables()
        self.feature_tables[name] = table
        return table

    def drop_feature_table(self, name: str) -> None:
        table = self.feature_tables.pop(name)
        table.drop_tables()

    def _get_connection(self) -> None:
        conn = sqlite3.connect(self.path, uri=True)
        conn.enable_load_extension(True)
        # Spatialite used for rtree-based functions (MinX, etc). Can eventually
        # replace or make configurable with other extensions.
        conn.load_extension("mod_spatialite.so")
        conn.row_factory = self._dict_factory
        self.conn = conn

    @contextlib.contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        # FIXME: monitor connection and ensure that it is good. Handle
        #        in-memory case.
        yield self.conn
        self.conn.commit()
        # FIXME: downsides of not calling conn.close? It's necessary to note
        #        call conn.close for in-memory databases. May want to change
        #        this behavior depending on whether the db is on-disk or
        #        in-memory.

    def _setup_database(self) -> None:
        if self.path is None:
            # TODO: revisit this behavior. Creating a temporary file by default
            #       may be undesirable.
            # Create a temporary path, get the name
            _, path = tempfile.mkstemp(suffix=".gpkg")
            self.path = str(path)
            # Delete the path to prepare for fresh db
            os.remove(path)

        if self._is_empty_database():
            self._create_database()

    def _is_empty_database(self) -> bool:
        with self.connect() as conn:
            query = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
            try:
                next(query)
                return False
            except StopIteration:
                return True

    def _create_database(self) -> None:
        with self.connect() as conn:
            # Set the format metadata
            conn.execute(f"PRAGMA application_id = {GPKG_APPLICATION_ID}")
            conn.execute(f"PRAGMA user_version = {GPKG_USER_VERSION}")

            # Create gpkg_contents table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gpkg_contents (
                    table_name TEXT,
                    data_type TEXT NOT NULL,
                    identifier TEXT UNIQUE,
                    description TEXT DEFAULT '',
                    last_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    min_x DOUBLE,
                    min_y DOUBLE,
                    max_x DOUBLE,
                    max_y DOUBLE,
                    srs_id INTEGER,
                    PRIMARY KEY (table_name)
                )
            """
            )

            # Create gpkg_extensions table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gpkg_extensions(
                    table_name TEXT,
                    column_name TEXT,
                    extension_name TEXT NOT NULL,
                    definition TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    UNIQUE (table_name, column_name, extension_name)
                )
            """
            )

            # Create gpkg_geometry_columns table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gpkg_geometry_columns(
                    table_name TEXT UNIQUE NOT NULL,
                    column_name TEXT NOT NULL,
                    geometry_type_name TEXT NOT NULL,
                    srs_id INTEGER NOT NULL,
                    z TINYINT NOT NULL,
                    m TINYINT NOT NULL,
                    PRIMARY KEY (table_name, column_name)
                )
            """
            )

            # Create gpkg_ogr_contents table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gpkg_ogr_contents(
                    table_name TEXT NOT NULL,
                    feature_count INTEGER DEFAULT NULL,
                    PRIMARY KEY (table_name)
                )
            """
            )

            # Create gpkg_spatial_ref_sys
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gpkg_spatial_ref_sys(
                    srs_name TEXT NOT NULL,
                    srs_id INTEGER NOT NULL,
                    organization TEXT NOT NULL,
                    organization_coordsys_id INTEGER NOT NULL,
                    definition TEXT NOT NULL,
                    description TEXT,
                    PRIMARY KEY (srs_id)
                )
            """
            )

    def copy(self, path: str) -> GeoPackage:
        """Copies the current GeoPackage to a new location and returns a new instance
        of a GeoPackage. A convenient way to create an in-memory GeoPackage, as
        path can be any SQLite-compatible connection string, including
        :memory:.

        :param path: Path to the new database. Any SQLite connection string can
                     be used.
        :type path: str

        """
        # TODO: catch the "memory" string and ensure that it includes a name
        #       and shared cache. Our strategy requires reconnecting to the db,
        #       so it must persist in memory.

        new_conn = sqlite3.connect(path)
        new_conn.enable_load_extension(True)
        # Spatialite used for rtree-based functions (MinX, etc). Can eventually
        # replace or make configurable with other extensions.
        new_conn.load_extension("mod_spatialite.so")

        with self.connect() as conn:
            # Set row_factory to none for iterdumping
            conn.row_factory = None

            # Copy over all tables but not indices
            for line in conn.iterdump():
                # Skip all index creation - these should be recreated
                # afterwards
                if "CREATE TABLE" in line or "INSERT INTO" in line:
                    # TODO: derive index names from metadata table instead
                    if "idx_" in line:
                        continue
                    if "rtree_" in line:
                        continue
                if "COMMIT" in line:
                    continue
                new_conn.cursor().executescript(line)

            # Copy over all indices
            for line in conn.iterdump():
                # Recreate the indices
                if "CREATE TABLE" in line or "INSERT INTO" in line:
                    if "idx_" in line:
                        new_conn.cursor().executescript(line)
                if "COMMIT" in line:
                    continue

            # TODO: rtree strategy is different? Why?
            # for line in conn.iterdump():
            #     # Recreate the indices
            #     if "CREATE TABLE" in line or "INSERT INTO" in line:
            #         if "rtree_" in line:
            #             new_conn.cursor().executescript(line)
            #     if "COMMIT" in line:
            #         continue
            conn.row_factory = self._dict_factory

        new_db = GeoPackage(path)

        return new_db

    # TODO: Instead of 'Any', use Python types that can be deserialized from
    # sqlite
    @staticmethod
    def _dict_factory(
        cursor: sqlite3.Cursor, row: sqlite3.Row
    ) -> Dict[str, Any]:
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
