"""Wraps various readers/writers for different geospatial formats with a focus
on low-memory reading."""
import os
from typing import Iterable, List, Optional

import fiona  # type: ignore

from unweaver.exceptions import UnrecognizedFileFormat
from unweaver.geojson import LineString
from unweaver.graph_types import EdgeTuple


def edge_generator(
    path: str,
    precision: int,
    changes_sign: Optional[List[str]] = None,
    add_reverse: bool = False,
) -> Iterable[EdgeTuple]:
    layer = os.path.splitext(os.path.basename(path))[0]
    if changes_sign is None:
        changes_sign = []

    try:
        with fiona.open(path) as handle:
            for f in handle:
                # TODO: log total number of edges skipped and inform user.
                # TODO: split MultiLineStrings into multiple LineStrings?
                if f["geometry"]["type"] != "LineString":
                    continue
                u, v, props = edge_from_feature(f, layer, precision)
                yield u, v, props
                if add_reverse:
                    props = {**props}
                    props["geom"] = reverse_linestring(props["geom"])
                    for change_sign in changes_sign:
                        if change_sign in props:
                            props[change_sign] = -1 * props[change_sign]
                    yield v, u, props
    except fiona.errors.DriverError:
        raise UnrecognizedFileFormat(
            "{} has an unrecognized format.".format(path)
        )


def create_node_id(lon: float, lat: float, precision: int) -> str:
    return f"{round(lon, precision)}, {round(lat, precision)}"


def edge_from_feature(feature: dict, layer: str, precision: int) -> EdgeTuple:
    props = {k: v for k, v in feature["properties"].items() if v is not None}
    props["geom"] = LineString(feature["geometry"]["coordinates"])
    props["_layer"] = layer
    props = {k: v for k, v in props.items() if v is not None}

    # Handle case where _u and _v have been provided by an upstream source:
    # just use their id. These data are removed from the properties of the
    # input data so that there is a single source of truth on graph node
    # identities.

    if "_u" in props:
        u = props.pop("_u")
    else:
        lon, lat = feature["geometry"]["coordinates"][0]
        u = create_node_id(lon, lat, precision)

    if "_v" in props:
        v = props.pop("_v")
    else:
        lon, lat = feature["geometry"]["coordinates"][-1]
        v = create_node_id(lon, lat, precision)

    return u, v, props


def reverse_linestring(linestring: LineString) -> LineString:
    return LineString(list(reversed(linestring.coordinates)))
