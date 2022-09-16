import os
from typing import Iterable, List, Optional

from click._termui_impl import ProgressBar

from unweaver.constants import DB_PATH
from unweaver.graphs.digraphgpkg import DiGraphGPKG

from .graph_builder import GraphBuilder
from .get_layers_paths import get_layers_paths


def build_graph(
    path: str,
    precision: int = 7,
    changes_sign: Optional[List[str]] = None,
    counter: Optional[ProgressBar] = None,
) -> DiGraphGPKG:
    """Build a graph in a project directory.

    :param path: Path to the project directory.
    :param precision: Rounding precision for whether to connect two
    LineStrings end-to-end. Defaults to about 10 cm.
    :param changes_sign: A list of numeric edge fields whose values should
    change sign when traversed in the "reverse" direction. An incline value
    is an example of this: uphill is positive, downhill negative.
    :param counter: An optional Click counter.

    """
    builder = GraphBuilder(precision=precision, changes_sign=changes_sign)

    paths = get_layers_paths(path)
    db_path = os.path.join(path, DB_PATH)

    for path in paths:
        builder.add_edges_from(path, counter=counter)

    builder.finalize_db(db_path)

    return builder.G
