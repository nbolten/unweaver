# Imported annotations from __future__ so that method returning class instance
# can be hinted
from __future__ import annotations
from typing import Any, Collection, Dict, Iterable, List
import sqlite3

from unweaver.geopackage import GeoPackage, GeoPackageGeoms
from unweaver.graph_types import EdgeTuple
from .edge_table import EdgeTable
from .node_table import NodeTable


class GeoPackageNetwork:
    def __init__(self, path: str = None, srid: int = 4326):
        self.path = path
        self.gpkg = GeoPackage(path=path)
        # TODO: handle reprojection during addition of features
        self.srid = srid

        # TODO: handle recognition of existing geopackage (with expected
        #       tables) vs. initializing one from scratch.
        self._create_graph_tables()
        self.edges = EdgeTable(
            self.gpkg, "edges", GeoPackageGeoms.LINESTRING, srid=srid
        )
        self.nodes = NodeTable(
            self.gpkg, "nodes", GeoPackageGeoms.POINT, srid=srid
        )
        self.gpkg.feature_tables["edges"] = self.edges
        self.gpkg.feature_tables["nodes"] = self.nodes

    def copy(self, path: str) -> GeoPackageNetwork:
        self.gpkg.copy(path)
        return GeoPackageNetwork(path, srid=self.srid)

    def _create_graph_tables(self) -> None:
        # TODO: consider creating metadata table to support multiple
        #       feature_tables, create edges view? Benchmark performance.
        #       Should be ~2X slowdown, but is more flexible and smaller
        #       change, easier to add/remove from a GeoPackage.
        try:
            with self.gpkg.connect() as conn:
                edges_table_query = conn.execute(
                    """
                    SELECT table_name
                      FROM gpkg_contents
                     WHERE table_name = 'edges'
                    """
                )
                next(edges_table_query)
        except StopIteration:
            self.gpkg.add_feature_table(
                "edges", GeoPackageGeoms.LINESTRING, self.srid
            )

        try:
            with self.gpkg.connect() as conn:
                nodes_table_query = conn.execute(
                    """
                    SELECT table_name
                      FROM gpkg_contents
                     WHERE table_name = 'nodes'
                    """
                )
                next(nodes_table_query)
        except StopIteration:
            self.gpkg.add_feature_table(
                "nodes", GeoPackageGeoms.POINT, self.srid
            )

        with self.gpkg.connect() as conn:
            try:
                conn.execute("ALTER TABLE nodes ADD _n TEXT")
                conn.execute("ALTER TABLE edges ADD _u TEXT")
                conn.execute("ALTER TABLE edges ADD _v TEXT")
            except sqlite3.OperationalError:
                # Ignore case where columns already exist
                pass

        with self.gpkg.connect() as conn:
            # NOTE: create these indices later to improve performance?
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS nodes_n_index
                                         ON nodes (_n)
            """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS edges_u_index ON edges (_u)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS edges_v_index ON edges (_v)"
            )
            conn.execute(
                """CREATE UNIQUE INDEX IF NOT EXISTS edges_uv_index
                                                           ON edges (_u, _v)
            """
            )

    def has_node(self, n: str) -> bool:
        """Check whether a node with id 'n' is in the graph.
        :param n: The node id.
        """
        with self.gpkg.connect() as conn:
            query = conn.execute("SELECT _n FROM nodes WHERE _n = ?", (n,))
            result = query.fetchone()
        if result is None:
            return False
        return True

    def add_edges(
        self, edges: Iterable[EdgeTuple], batch_size: int = 10000, **attr: Any
    ) -> None:
        """Add edges to the network.
        :param edges: an iterable of 2-tuples or 3-tuples representing (u, v)
                      or (u, v, d) edges (as expected by NetworkX). Iterable
                      can mix both edge types.
        :param batch_size: Size of batches to write downstream.
        :param attr: Any default attributes to add to all edges. If any
                     attributes conflict with edge data, edge data supercedes.
        """
        node_queue: List[Dict[str, Collection[str]]] = []
        edge_queue: List[dict] = []

        for u, v, edge_data in edges:
            if len(edge_queue) > batch_size:
                self.edges.write_features(edge_queue, batch_size=batch_size)
                self.nodes.write_features(node_queue, batch_size=batch_size)
                node_queue = []
                edge_queue = []

            d: Dict[str, Any] = {}
            d["_u"] = u
            d["_v"] = v
            for key, value in edge_data.items():
                if key == "geom":
                    geom: dict = value
                    d[key] = geom
                else:
                    d[key] = value

            for key, value in attr.items():
                d[key] = value

            edge_queue.append(d)

            # TODO: create a dataclass for queued nodes
            if "geom" in d:
                node_queue.append(
                    {
                        "_n": u,
                        "geom": {
                            "type": "Point",
                            "coordinates": d["geom"]["coordinates"][0],
                        },
                    }
                )
                node_queue.append(
                    {
                        "_n": v,
                        "geom": {
                            "type": "Point",
                            "coordinates": d["geom"]["coordinates"][-1],
                        },
                    }
                )

        self.edges.write_features(edge_queue, batch_size=batch_size)
        self.nodes.write_features(node_queue, batch_size=batch_size)
