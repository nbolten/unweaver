from unweaver.shortest_path import shortest_path, NoPathError


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

    try:
        cost, path, edges = shortest_path(G, lon1, lat1, lon2, lat2, cost_function)
    except NoPathError:
        return {"status": "Failed", "msg": "No path"}

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
