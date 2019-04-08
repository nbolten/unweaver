from flask import g, jsonify

from ...algorithms.shortest_path import route_legs, waypoint_legs, NoPathError


def directions_view(view_args, cost_function, directions_function):
    lon1 = view_args["lon1"]
    lat1 = view_args["lat1"]
    lon2 = view_args["lon2"]
    lat2 = view_args["lat2"]

    legs = waypoint_legs(g.G, [[lon1, lat1], [lon2, lat2]], cost_function)
    for i, (wp1, wp2) in enumerate(legs):
        if wp1 is None:
            return jsonify(
                {
                    "status": "InvalidWaypoint",
                    "msg": "Cannot route from waypoint {}".format(i + 1),
                    "status_data": {"index": i},
                }
            )
        if wp2 is None:
            return jsonify(
                {
                    "status": "InvalidWaypoint",
                    "msg": "Cannot route to waypoint {}".format(i + 2),
                    "status_data": {"index": i + 1},
                }
            )

    try:
        cost, path, edges = route_legs(g.G, legs, cost_function)
    except NoPathError:
        return jsonify({"status": "NoPath", "msg": "No path found."})

    origin = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon1, lat1]},
        "properties": {},
    }
    destination = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon2, lat2]},
        "properties": {},
    }

    directions = directions_function(origin, destination, cost, path, edges)

    return jsonify(directions)
