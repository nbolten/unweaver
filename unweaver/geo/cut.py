"""Function to cut Shapely LineStrings at a distance along them."""
from typing import List, Iterator, Tuple

from shapely.geometry import LineString  # type: ignore


def cut(line: LineString, distance: float) -> List[Iterator[float]]:
    """Cuts a Shapely LineString at the stated distance. Returns a list of two
    new LineStrings for valid inputs. If the distance is 0, negative, or longer
    than the LineString, a list with the original LineString is produced.

    :param line: LineString to cut.
    :param distance: Distance along the line where it will be cut.

    """
    if distance <= 0.0 or distance >= line.length:
        return list(line.coords)
    # coords = list(line.coords)
    coords = line.coords

    pd = 0.0
    last = coords[0]
    for i, p in enumerate(coords):
        if i == 0:
            continue
        pd += _point_distance(last, p)

        if pd == distance:
            return [coords[: i + 1], coords[i:]]
        if pd > distance:
            cp = line.interpolate(distance)
            return [coords[:i] + [(cp.x, cp.y)], [(cp.x, cp.y)] + coords[i:]]

        last = p
    # If the code reaches this point, we've hit a floating point error or
    # something, as the total estimated distance traveled is less than the
    # distance specified and the distance specified is less than the length of
    # the geometry, so there's some small gap. The approach floating around
    # online is to use linear projection to find the closest point to the given
    # distance, but this is not robust against complex, self-intersection
    # lines. So, instead: we just assume it's between the second to last and
    # last point.
    cp = line.interpolate(distance)
    return [coords[:i] + [(cp.x, cp.y)], [(cp.x, cp.y)] + coords[i:]]


def cut_off(line: LineString, distance: float) -> List[List[float]]:
    """Cuts a Shapely LineString at the stated distance. Returns a list of two
    new LineStrings for valid inputs. If the distance is 0, negative, or longer
    than the LineString, a list with the original LineString is produced.

    :param line: LineString to cut.
    :param distance: Distance along the line where it will be cut.

    """
    if distance <= 0.0 or distance >= line.length:
        return list(line.coords)
    coords = line.coords

    pd = 0.0
    last = coords[0]
    for i, p in enumerate(coords):
        if i == 0:
            continue
        pd += _point_distance(last, p)

        if pd == distance:
            return [coords[: i + 1], coords[i:]]
        if pd > distance:
            cp = line.interpolate(distance)
            return coords[:i] + [(cp.x, cp.y)]

        last = p
    # If the code reaches this point, we've hit a floating point error or
    # something, as the total estimated distance traveled is less than the
    # distance specified and the distance specified is less than the length of
    # the geometry, so there's some small gap. The approach floating around
    # online is to use linear projection to find the closest point to the given
    # distance, but this is not robust against complex, self-intersection
    # lines. So, instead: we just assume it's between the second to last and
    # last point.
    cp = line.interpolate(distance)
    return coords[:i] + [(cp.x, cp.y)]


def _point_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Distance between two points (l2 norm).

    :param p1: Point 1.
    :param p2: Point 2.

    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    return (dx ** 2 + dy ** 2) ** 0.5
