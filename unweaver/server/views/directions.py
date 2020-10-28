from flask import g
from marshmallow import Schema, fields

from ...algorithms.shortest_path import route_legs, waypoint_legs, NoPathError


from .base_view import BaseView


class DirectionsSchema(Schema):
    lon1 = fields.Float(required=True)
    lat1 = fields.Float(required=True)
    lon2 = fields.Float(required=True)
    lat2 = fields.Float(required=True)


class DirectionsView(BaseView):
    view_name = "directions"
    schema = DirectionsSchema

    def run_analysis(self, arguments, cost_function):
        lon1 = arguments["lon1"]
        lat1 = arguments["lat1"]
        lon2 = arguments["lon2"]
        lat2 = arguments["lat2"]

        legs = waypoint_legs(g.G, [[lon1, lat1], [lon2, lat2]], cost_function)

        for i, (wp1, wp2) in enumerate(legs):
            if wp1 is None or wp2 is None:
                return ("InvalidWaypoint",)

        try:
            cost, path, edges = route_legs(
                g.G, legs, self.precalculated_cost_function
            )
        except NoPathError:
            return ("NoPath",)

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

        return ("Ok", g.G, origin, destination, cost, path, edges)
