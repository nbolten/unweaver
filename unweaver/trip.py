from unweaver.shortest_path import route_legs, waypoint_legs, NoPathError


def get_trip(G, profile, webargs):
    try:
        lon1 = webargs.pop("lon1")
        lat1 = webargs.pop("lat1")
        lon2 = webargs.pop("lon2")
        lat2 = webargs.pop("lat2")
    except KeyError:
        # FIXME: should produce specific exceptions / status to pass to directions
        # function for consistent response messages.
        return jsonify({"status": "Failed", "msg": "Missing location inputs"}), 400

    cost_function = profile.cost_function_generator(**webargs)
    directions_function = profile.directions

    legs = waypoint_legs(G, [[lon1, lat1], [lon2, lat2]], cost_function)
    for i, (wp1, wp2) in enumerate(legs):
        if wp1 is None:
            return {
                "status": "InvalidWaypoint",
                "msg": "Cannot route from waypoint {}".format(i + 1),
                "status_data": {"index": i},
            }
        if wp2 is None:
            return {
                "status": "InvalidWaypoint",
                "msg": "Cannot route to waypoint {}".format(i + 2),
                "status_data": {"index": i + 1},
            }

    try:
        cost, path, edges = route_legs(G, legs, cost_function)
    except NoPathError:
        return {"status": "NoPath", "msg": "No path found."}

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

    return directions
