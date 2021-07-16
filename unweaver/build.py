import os
from typing import Iterable, List, Optional

from click._termui_impl import ProgressBar
import entwiner


from unweaver.constants import DB_PATH
from unweaver.exceptions import MissingLayersError


def get_layers_paths(path: str) -> List[str]:
    layers_path = os.path.join(path, "layers")
    if not os.path.exists(layers_path):
        raise MissingLayersError("layers directory not found.")

    layers_paths = [
        os.path.join(layers_path, f)
        for f in os.listdir(layers_path)
        if f.endswith("geojson")
    ]
    if not layers_paths:
        raise MissingLayersError("No GeoJSON files in layers directory.")

    return layers_paths


def build_graph(
    path: str,
    precision: int = 7,
    changes_sign: Iterable[str] = None,
    counter: Optional[ProgressBar] = None,
) -> entwiner.DiGraphDB:
    builder = entwiner.GraphBuilder(
        precision=precision, changes_sign=changes_sign
    )
    builder.create_temporary_db()

    paths = get_layers_paths(path)
    db_path = os.path.join(path, DB_PATH)

    for path in paths:
        builder.add_edges_from(path, counter=counter)

    builder.finalize_db(db_path)

    return builder.G
