import os
from typing import List

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
