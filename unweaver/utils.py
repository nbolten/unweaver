import math
from typing import Any, Sequence, Tuple


RADIUS = 6371000  # Radius of the earth in meters


def haversine(coords: Sequence[Tuple[float, float]]) -> float:
    # Given a list of coordinates (e.g. linestring.coords), calculate the
    # great circle length of the line, in meters

    d_tot = 0.0
    for i, coord in enumerate(coords):
        if i == 0:
            continue
        last_coord = coords[i - 1]

        lon1, lat1 = last_coord
        lon2, lat2 = coord

        dlon = math.radians(lon2 - lon1)
        dlat = math.radians(lat2 - lat1)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat2))
            * math.cos(math.radians(lat1))
            * math.sin(dlon / 2) ** 2
        )

        d = RADIUS * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d_tot += d

    return d_tot


def sqlite_type(value: Any) -> str:
    if type(value) == int:
        return "INTEGER"
    elif type(value) == float:
        return "REAL"
    else:
        return "TEXT"
