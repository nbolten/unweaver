from flask import g, jsonify
from marshmallow import Schema
from webargs.flaskparser import use_args

from ... import default_profile_functions


class BaseView:
    # TODO: require definition of view name
    view_name = None

    def __init__(self, profile):
        self.profile = profile

    @property
    def cost_function_generator(self):
        return self.profile.get(
            "cost_function_generator",
            default_profile_functions.cost_function_generator,
        )

    @property
    def precalculated_cost_function(self):
        if "precalculate" in self.profile:
            weight_column = "_weight_{}".format(self.profile["id"])
            return lambda u, v, d: d.get(weight_column, None)
        else:
            return None

    def run_analysis(self, arguments, cost_function):
        raise NotImplementedError

    @property
    def interpretation_function_name(self):
        return f"{self.view_name}_function"

    def interpret_result(self, result):
        interpretation_function = self.profile.get(
            self.interpretation_function_name,
            getattr(
                default_profile_functions, self.interpretation_function_name
            ),
        )
        result = interpretation_function(*result)
        return jsonify(result)

    def create_view(self):
        profile_args = {
            arg["name"]: arg["type"] for arg in self.profile.get("args", [])
        }
        profile_schema = Schema.from_dict(profile_args)

        class CombinedSchema(self.schema, profile_schema):
            pass

        @use_args(CombinedSchema(), location="query")
        def view(args):
            if g.get("failed_graph", False):
                return jsonify({"status": "NoGraph"})
            cost_args = {k: v for k, v in args.items() if k in profile_args}
            cost_function = self.cost_function_generator(**cost_args)
            analysis_result = self.run_analysis(args, cost_function)

            return self.interpret_result(analysis_result)

        return view
