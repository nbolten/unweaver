"""Wraps various readers/writers for different geospatial formats with a focus
on low-memory reading."""
import os
from typing import Iterable, List, Optional

import fiona

from unweaver.exceptions import UnrecognizedFileFormat
from unweaver.geojson import Feature, LineString
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

    def edge_from_feature(feature: Feature) -> EdgeTuple:
        props = {k: v for k, v in f["properties"].items() if v is not None}
        props["geom"] = LineString(f["geometry"]["coordinates"])
        props["_layer"] = layer
        props = {k: v for k, v in props.items() if v is not None}

        u = ", ".join(
            [str(round(c, precision)) for c in f["geometry"]["coordinates"][0]]
        )
        v = ", ".join(
            [
                str(round(c, precision))
                for c in f["geometry"]["coordinates"][-1]
            ]
        )

        return u, v, props

    try:
        with fiona.open(path) as handle:
            for f in handle:
                # TODO: log total number of edges skipped and inform user.
                # TODO: split MultiLineStrings into multiple LineStrings?
                if f["geometry"]["type"] != "LineString":
                    continue
                u, v, props = edge_from_feature(f)
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


def reverse_linestring(linestring: LineString) -> LineString:
    return LineString(list(reversed(linestring.coordinates)))
