import os

import entwiner


class MissingLayersError(Exception):
    pass


def build_graph(path, changes_sign=None):
    if changes_sign is None:
        changes_sign = []
    layers_path = os.path.join(path, "layers")
    if not os.path.exists(layers_path):
        raise MissingLayersError("layers directory not found.")

    layers_files = [
        os.path.join(layers_path, f)
        for f in os.listdir(layers_path)
        if f.endswith("geojson")
    ]
    if not layers_files:
        raise MissingLayersError("No GeoJSON files in layers directory.")

    # TODO: specify behavior when graph already exists
    db_path = os.path.join(path, "graph.db")
    G = entwiner.build.create_graph(layers_files, db_path, changes_sign=changes_sign)

    return G
