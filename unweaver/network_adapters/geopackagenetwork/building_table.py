from typing import Any, Dict, Generator, Iterable, List, Tuple
from unweaver.databases.geopackage.feature_table import FeatureTable
from unweaver.graph_types import BuildingData, BuildingTuple

"""
Notes:
    - Consider putting this in its own module (e.g. in a "unweaver/semantic_table" folder)
    - Write some tests for this class (and better tests for other classes)
    - Look at OSM's "building" tag for more information
    - Consider how someone can declare this into the actual database
    - Consider what the user needs to provide us to create a building
        - E.g. assign a weight to a path based on how close it is to a building
    - Design the signature of the (enrichment) function

Features of a building:
    - nodes for entrances and exits
    - height
    - type of building (e.g. hospital, store, etc.)
    - TODO: add more ...
"""

class BuildingTable(FeatureTable):
    building_key = "_b"

    def dwithin_buildings(
        self, lon: float, lat: float, distance: float, sort: bool = False
    ) -> Iterable[BuildingTuple]:
        rows = super().dwithin(lon, lat, distance, sort=sort)
        return (self._graph_format(row) for row in rows)
    
    def update_buildings(self, nbunch: Iterable[BuildingTuple]) -> None:
        serialized = [(n, self.serialize_row(d)) for n, d in nbunch]
        super().update_batch(serialized)
    
    def update_building(self, key: str, d: dict) -> None:
        self.update_buildings([(key, d)])
    
    def get_building(self, b: str) -> dict:
        with self.gpkg.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM {self.name} WHERE {self.building_key} = ?
            """,
                (b,),
            )

            return self.deserialize_row(next(rows))
    
    def delete(self, building: str):
        with self.gpkg.connect() as conn:
            conn.execute(
                f"""
                DELETE FROM {self.name} WHERE {self.building_key} = ?
            """,
                (building,),
            )
    
    def iter_buildings(self) -> Generator[BuildingTuple, None, None]:
        for row in super().__iter__():
            yield self._graph_format(row)
    
    def _graph_format(self, row: dict) -> BuildingTuple:
        b = row.pop(self.building_key)
        return b, row

    def _table_format(
        self, bbunch: Iterable[BuildingTuple]
    ) -> Generator[dict, None, None]:
        for b, d in bbunch:
            yield {self.building_key: b, **d}