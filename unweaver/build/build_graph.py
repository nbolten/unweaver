import os
from typing import Iterable, Optional

from click._termui_impl import ProgressBar

from unweaver.constants import DB_PATH
from unweaver.graphs.digraphgpkg import DiGraphGPKG

from .graph_builder import GraphBuilder
from .get_layers_paths import get_layers_paths


def build_graph(
    path: str,
    precision: int = 7,
    changes_sign: Iterable[str] = None,
    counter: Optional[ProgressBar] = None,
) -> DiGraphGPKG:
    builder = GraphBuilder(precision=precision, changes_sign=changes_sign)

    paths = get_layers_paths(path)
    db_path = os.path.join(path, DB_PATH)

    for path in paths:
        builder.add_edges_from(path, counter=counter)

    builder.finalize_db(db_path)

    return builder.G
