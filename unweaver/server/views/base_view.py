from typing import Any, Callable, Optional, Type, Union

from flask import g, jsonify
from marshmallow import Schema
from webargs.flaskparser import use_args

from unweaver.graph_types import CostFunction
from unweaver.profile import Profile


class BaseView:
    view_name: Optional[str] = None
    schema: Type[Schema]

    def __init__(self, profile: Profile):
        if self.view_name is None:
            raise AttributeError(
                "BaseView subclass must have view_name class attribute."
            )
        self.profile = profile

    @property
    def cost_function_generator(self) -> Callable[..., CostFunction]:
        return self.profile["cost_function"]

    @property
    def precalculated_cost_function(self) -> Union[CostFunction, None]:
        if "precalculate" in self.profile:
            weight_column = f"_weight_{self.profile['id']}"
            return lambda u, v, d: d.get(weight_column, None)
        else:
            return None

    # FIXME: don't constrain to Any type: constrain to a union of:
    #   Tuple[str],
    #   An extension of Tuple[str, ...]
    #   (or change return type to make this more straightforward).
    def run_analysis(
        self, arguments: dict, cost_function: CostFunction
    ) -> Any:
        raise NotImplementedError

    def interpret_result(self, result: Any) -> str:
        if self.view_name == "shortest_path":
            interpretation_function = self.profile["shortest_path"]
        elif self.view_name == "shortest_path_tree":
            interpretation_function = self.profile["shortest_path_tree"]
        elif self.view_name == "reachable_tree":
            interpretation_function = self.profile["reachable_tree"]
        else:
            interpretation_function = self.profile["shortest_path"]
        interpreted_result = interpretation_function(*result)
        return interpreted_result

    def create_view(self) -> Callable:
        profile_args = {
            arg["name"]: arg["type"] for arg in self.profile.get("args", [])
        }
        profile_schema = Schema.from_dict(profile_args)

        # Have to ignore type - profile_schema from_dict fails static analysis
        class CombinedSchema(self.schema, profile_schema):  # type: ignore
            pass

        @use_args(CombinedSchema(), location="query")
        def view(args: dict) -> Any:
            if g.get("failed_graph", True):
                return jsonify({"code": "NoGraph"})
            cost_args = {k: v for k, v in args.items() if k in profile_args}
            cost_function = self.cost_function_generator(g.G, **cost_args)
            analysis_result = self.run_analysis(args, cost_function)

            code = analysis_result[0]
            if code in ("NoPath", "InvalidWaypoint"):
                return jsonify({"code": code})

            return jsonify(self.interpret_result(analysis_result))

        return view
