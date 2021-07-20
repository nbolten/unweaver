import os
import shutil
import tempfile
from typing import List, Optional, Type

from click._termui_impl import ProgressBar

from unweaver.constants import BATCH_SIZE
from unweaver.graphs.digraphgpkg import DiGraphGPKG
from unweaver.io import edge_generator


class GraphBuilder:
    def __init__(
        self,
        graph_class: Type[DiGraphGPKG] = DiGraphGPKG,
        precision: int = 7,
        changes_sign: Optional[List[str]] = None,
    ):
        if changes_sign is None:
            changes_sign = []

        self.precision = precision
        self.changes_sign = changes_sign
        self.graph_class = graph_class
        self.tempfile = ""

        self.create_temporary_db()

    # TODO: automatic cleanup if this fails.
    def create_temporary_db(self) -> None:
        # self.G = self.graph_class.create_graph()
        _, path = tempfile.mkstemp()
        path = str(path)
        os.remove(path)
        path = f"{path}.gpkg"
        G = self.graph_class.create_graph(path=path)
        self.tempfile = path
        self.G = G

    def finalize_db(self, path: str) -> None:
        # FIXME: implement proper interface / paradigm for overwriting
        #        GeoPackages. Consider creating path.gpkg.build temporary file

        # TODO: place the rtree step somewhere else?
        self.G.network.edges.add_rtree()
        self.G.network.nodes.add_rtree()

        if os.path.exists(path):
            os.remove(path)
        shutil.move(self.tempfile, path)
        self.G.network.gpkg.path = path
        self.tempfile = ""

    def get_G(self) -> DiGraphGPKG:
        return self.G

    def add_edges_from(
        self,
        path: str,
        batch_size: int = BATCH_SIZE,
        counter: ProgressBar = None,
    ) -> None:
        edge_gen = edge_generator(
            path,
            precision=self.precision,
            changes_sign=self.changes_sign,
            add_reverse=True,
        )
        self.G.add_edges_from(
            edge_gen, _batch_size=batch_size, counter=counter
        )
