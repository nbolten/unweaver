from typing import Any, Dict, Generator, Iterable, List, Tuple

from click._termui_impl import ProgressBar

from unweaver.databases.geopackage.feature_table import FeatureTable
from unweaver.graph_types import EdgeData, EdgeTuple

# FIXME: define Row type to make serialization/deserializaiton and mapping
# easier to type


class EdgeTable(FeatureTable):
    u_key = "_u"
    v_key = "_v"

    def write_features(
        self,
        features: Iterable[dict],
        batch_size: int = 10000,
        counter: ProgressBar = None,
    ) -> None:
        # FIXME: should fill a nodes queue instead of realizing a full list at
        # this step
        ways_queue: List[Dict[str, Any]] = []
        nodes_queue: List[Dict[str, Any]] = []

        for feature in features:
            if len(ways_queue) >= batch_size:
                super().write_features(ways_queue, 10000, counter)
                self.gpkg.feature_tables["nodes"].write_features(nodes_queue)
                ways_queue = []
                nodes_queue = []
            ways_queue.append(feature)
            u_feature = {"_n": feature[self.u_key]}
            v_feature = {"_n": feature[self.v_key]}
            if self.geom_column in feature:
                u_feature[self.geom_column] = {
                    "type": "Point",
                    "coordinates": feature["geom"].coordinates[0],
                }
                v_feature[self.geom_column] = {
                    "type": "Point",
                    "coordinates": feature["geom"].coordinates[-1],
                }
            nodes_queue.append(u_feature)
            nodes_queue.append(v_feature)

        self.gpkg.feature_tables["nodes"].write_features(nodes_queue)
        super().write_features(ways_queue, batch_size, counter)

    def dwithin_edges(
        self, lon: float, lat: float, distance: float, sort: bool = False
    ) -> Iterable[EdgeTuple]:
        rows = super().dwithin(lon, lat, distance, sort=sort)
        return (self._graph_format(row) for row in rows)

    def update_edges(self, ebunch: Iterable[EdgeTuple]) -> None:
        with self.gpkg.connect() as conn:
            fids = []
            # TODO: investigate whether this is a slow step
            for u, v, d in ebunch:
                # TODO: use different column format for this step? No need to
                # get a dictionary as query output first.
                fid = conn.execute(
                    f"""
                    SELECT fid
                      FROM {self.name}
                     WHERE {self.u_key} = ?
                       AND {self.v_key} = ?""",
                    (u, v),
                ).fetchone()["fid"]
                fids.append(fid)

        ddicts = []
        for u, v, d in ebunch:
            ddict = self.serialize_row(next(self._table_format(((u, v, d),))))
            ddicts.append(ddict)

        super().update_batch(zip(fids, ddicts))

    def update_edge(self, u: str, v: str, d: EdgeData) -> None:
        self.update_edges([(u, v, d)])

    def successor_nodes(self, n: str = None) -> List[str]:
        with self.gpkg.connect() as conn:
            if n is None:
                rows = conn.execute(
                    f"SELECT DISTINCT {self.v_key} FROM {self.name}"
                )
            else:
                rows = conn.execute(
                    f"""
                    SELECT {self.v_key}
                      FROM {self.name}
                     WHERE {self.u_key} = ?""",
                    (n,),
                )
            # TODO: performance increase by temporary changing row handler?
            ns = [r[self.v_key] for r in rows]
        return ns

    def predecessor_nodes(self, n: str = None) -> List[str]:
        with self.gpkg.connect() as conn:
            if n is None:
                rows = conn.execute(
                    f"SELECT DISTINCT {self.u_key} FROM {self.name}"
                )
            else:
                rows = conn.execute(
                    f"""
                    SELECT {self.u_key}
                      FROM {self.name}
                     WHERE {self.v_key} = ?""",
                    (n,),
                )
            # TODO: performance increase by temporary changing row handler?
            ns = [r[self.u_key] for r in rows]
        return ns

    def successors(self, n: str) -> List[Tuple[str, dict]]:
        with self.gpkg.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM {self.name} WHERE {self.u_key} = ?", (n,)
            )
            # TODO: performance increase by temporary changing row handler?
            ns = []
            for r in rows:
                u, v, d = self._graph_format(r)
                ns.append((v, self.deserialize_row(d)))
        return ns

    def predecessors(self, n: str) -> List[Tuple[str, dict]]:
        with self.gpkg.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM {self.name} WHERE {self.v_key} = ?", (n,)
            )
            # TODO: performance increase by temporary changing row handler?
            ns = [(r.pop(self.u_key), r) for r in rows]
        return ns

    def unique_predecessors(self, n: str = None) -> int:
        with self.gpkg.connect() as conn:
            if n is None:
                rows = conn.execute(
                    f"SELECT COUNT(DISTINCT({self.u_key})) c FROM {self.name}"
                )
            else:
                rows = conn.execute(
                    f"""
                    SELECT COUNT(DISTINCT({self.u_key})) c
                      FROM {self.name}
                     WHERE {self.v_key} = ?
                """,
                    (n,),
                )
            count = next(rows)["c"]
        return count

    def unique_successors(self, n: str = None) -> int:
        with self.gpkg.connect() as conn:
            if n is None:
                rows = conn.execute(
                    f"SELECT COUNT(DISTINCT({self.v_key})) c FROM {self.name}"
                )
            else:
                rows = conn.execute(
                    f"""
                    SELECT COUNT(DISTINCT({self.u_key})) c
                      FROM {self.name}
                     WHERE {self.u_key} = ?
                """,
                    (n,),
                )
            count = next(rows)["c"]
        return count

    def get_edge(self, u: str, v: str) -> dict:
        with self.gpkg.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT *
                  FROM {self.name}
                 WHERE {self.u_key} = ?
                   AND {self.v_key} = ?
            """,
                (u, v),
            )
            # TODO: performance increase by temporary changing row handler?
            return self.deserialize_row(next(rows))

    def delete(self, u: str, v: str) -> None:
        with self.gpkg.connect() as conn:
            conn.execute(
                f"""
                DELETE FROM {self.name}
                      WHERE {self.u_key} = ?
                        AND {self.v_key} = ?
            """,
                (u, v),
            )

    def iter_edges(self) -> Generator[EdgeTuple, None, None]:
        for row in super().__iter__():
            yield self._graph_format(row)

    def _graph_format(self, row: dict) -> EdgeTuple:
        u = row.pop(self.u_key)
        v = row.pop(self.v_key)
        return u, v, row

    def _table_format(
        self, ebunch: Iterable[EdgeTuple]
    ) -> Generator[dict, None, None]:
        for u, v, d in ebunch:
            ddict = {self.u_key: u, self.v_key: v, **d}
            if "fid" in ddict:
                ddict.pop("fid")
            yield ddict
