from flask import g, jsonify
from marshmallow import fields
from webargs.flaskparser import use_args

from ... import default_profile_functions

from .directions import directions_view
from .reachable import reachable_view
from .shortest_paths import shortest_paths_view


def add_view(
    app,
    view_name,
    profile,
    cost_function_generator,
    view_function,
    view_route_handler,
    view_args=None,
):
    # TODO: Could use url_for and a real Flask route template?
    profile_name = profile["id"]
    url = "/{}/{}.json".format(view_name, profile_name)

    profile_args = {}
    # FIXME: this implies that arg names should be unique, so why not make them
    # top-level keys in the JSON?
    if "args" in profile:
        for arg in profile["args"]:
            profile_args[arg["name"]] = arg["type"]

    # FIXME: ensure that user-defined arguments don't conflict with view-defined args
    combined_args = {}
    if view_args is not None:
        combined_args = {**profile_args, **view_args}

    @use_args(combined_args)
    def route_handler(args):
        # Handle common route and args validation checks
        if g.get("failed_graph", False):
            return jsonify(
                {"status": "NoGraph", "message": "Internal graph read error."}
            )

        # NOTE: validation errors are automatically passed down to flask's errorhandler
        # interface in server/app.py

        # Separate view-specific args from cost function args
        parsed_profile_args = {
            key: args[key] for key in profile_args.keys() if key in args
        }
        parsed_view_args = {key: args[key] for key in view_args.keys() if key in args}
        cost_function = cost_function_generator(**parsed_profile_args)
        return view_route_handler(parsed_view_args, cost_function, view_function)

    app.add_url_rule(url, "{}-{}".format(view_name, profile_name), route_handler)


def add_views(app, profile):
    directions_args = {
        "lon1": fields.Float(required=True),
        "lat1": fields.Float(required=True),
        "lon2": fields.Float(required=True),
        "lat2": fields.Float(required=True),
    }

    shortest_paths_args = {
        "lon": fields.Float(required=True),
        "lat": fields.Float(required=True),
        "max_cost": fields.Float(required=True),
    }

    reachable_args = {
        "lon": fields.Float(required=True),
        "lat": fields.Float(required=True),
        "max_cost": fields.Float(required=True),
    }

    cost_function_generator = profile.get(
        "cost_function", default_profile_functions.cost_function_generator
    )
    directions_function = profile.get(
        "directions", default_profile_functions.directions_function
    )
    shortest_paths_function = profile.get(
        "shortest_paths", default_profile_functions.shortest_paths_function
    )
    reachable_function = profile.get(
        "reachable", default_profile_functions.reachable_function
    )

    if profile["precalculate"]:
        weight_column = "_weight_{}".format(profile["id"])

        def precalculated_generator():
            return lambda u, v, d: d.get(weight_column, None)

        cost_function_generator = precalculated_generator

    add_view(
        app,
        "directions",
        profile,
        cost_function_generator,
        directions_function,
        directions_view,
        directions_args,
    )
    add_view(
        app,
        "shortest_paths",
        profile,
        cost_function_generator,
        shortest_paths_function,
        shortest_paths_view,
        shortest_paths_args,
    )
    add_view(
        app,
        "reachable",
        profile,
        cost_function_generator,
        reachable_function,
        reachable_view,
        reachable_args,
    )
