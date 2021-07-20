from typing import Any, Dict, Generator, Iterable

from unweaver.exceptions import NodeNotFound
from unweaver.databases.geopackage.feature_table import FeatureTable
from unweaver.graph_types import NodeTuple


class NodeTable(FeatureTable):
    node_key = "_n"

    def dwithin(
        self, lon: float, lat: float, distance: float, sort: bool = False
    ) -> Iterable[NodeTuple]:
        rows = super().dwithin(lon, lat, distance, sort=sort)
        return (self._graph_format(row) for row in rows)

    def update(self, nbunch: Iterable[NodeTuple]) -> None:
        super().update(self.serialize_row(self._table_format(nbunch)))

    def get_node(self, n: str) -> dict:
        with self.gpkg.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM {self.name} WHERE {self.node_key} = ?
            """,
                (n,),
            )
            # TODO: performance increase by temporary changing row handler?
            try:
                return self.deserialize_row(next(rows))
            except StopIteration:
                raise NodeNotFound()

    def insert(self, n: str, ddict: Dict[str, Any]) -> None:
        self.write_features({**ddict, self.node_key: n})
        with self.gpkg.connect() as conn:
            conn.execute(
                f"""
                INSERT INTO {self.name}
                DELETE FROM {self.name} WHERE {self.node_key} = ?
            """,
                (n,),
            )

    def delete(self, n: str) -> None:
        with self.gpkg.connect() as conn:
            conn.execute(
                f"""
                DELETE FROM {self.name} WHERE {self.node_key} = ?
            """,
                (n,),
            )

    def _graph_format(self, row: dict) -> NodeTuple:
        n = row.pop(self.node_key)
        return n, row

    def _table_format(
        self, nbunch: Iterable[NodeTuple],
    ) -> Generator[dict, None, None]:
        for n, d in nbunch:
            yield {self.node_key: n, **d}

    def __iter__(self) -> Generator[NodeTuple, None, None]:
        for row in super().__iter__():
            yield self._graph_format(row)
