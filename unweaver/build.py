import os

import fiona

import entwiner


class MissingLayersError(Exception):
    pass


def get_layers_paths(path):
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


def build_graph(path, precision=7, changes_sign=None, counter=None):
    builder = entwiner.GraphBuilder(precision=precision, changes_sign=changes_sign)
    builder.create_temporary_db()

    paths = get_layers_paths(path)

    db_path = os.path.join(path, "graph.db")
    for path in paths:
        builder.add_edges_from(path, counter=counter)

    builder.finalize_db(db_path)

    return builder.G


def n_features(paths):
    n = 0
    for path in paths:
        with fiona.open(path) as c:
            n += len(c)
