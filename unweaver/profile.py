import importlib.util
from functools import partial
import os
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Mapping,
    TypedDict,
    Union,
)

from marshmallow import Schema, fields, post_load

from unweaver.fields.eval import Eval
from unweaver.graph import CostFunction
from unweaver import default_profile_functions


class ProfileArg(TypedDict):
    name: str
    type: Union[fields.Field, type]


class RequiredProfile(TypedDict):
    name: str
    id: str


# TODO: Callable type signatures for directions, shortest_paths, reachabel
# TODO: cost_function property vs. cost_function_generator is ambiguous
class OptionalProfile(TypedDict, total=False):
    args: List[ProfileArg]
    static: Dict[str, fields.Field]
    precalculate: bool
    cost_function: Callable[..., CostFunction]
    directions: Callable
    shortest_paths: Callable
    reachable: Callable


class Profile(OptionalProfile, RequiredProfile):
    pass


class WorkingPathRequiredError(Exception):
    # TODO: inherit from more similar exception?
    pass


class ProfileArgSchema(Schema):
    name = fields.Str(required=True)
    type = Eval(required=True)


class ProfileSchema(Schema):
    args = fields.List(fields.Nested(ProfileArgSchema))
    cost_function = fields.Str()
    directions = fields.Str()
    name = fields.Str(required=True)
    id = fields.Str(required=True)
    precalculate = fields.Boolean()
    static = fields.Dict(
        keys=fields.Str(), values=fields.Field(), required=False
    )

    @post_load
    def make_profile(self, data: Mapping, **kwargs: Any) -> Profile:
        # TODO: investigate whether there's an elegant way to load the cost
        # function in a field type.
        if "working_path" not in self.context:
            # TODO: add useful message
            raise WorkingPathRequiredError()
        else:
            path = self.context["working_path"]

        cost_function: Callable[..., CostFunction]

        static = data.get("static", None)

        user_defined = {}
        for field_name in [
            "cost_function",
            "directions",
            "shortest_paths",
            "reachable",
        ]:
            function_name = field_name
            if function_name == "cost_function":
                function_name = "cost_fun_generator"

            if field_name in data:
                function = load_function(
                    path,
                    data[field_name],
                    "unweaver.user_defined",
                    function_name,
                    static=static,
                )
            else:
                function = getattr(default_profile_functions, function_name)

            user_defined[field_name] = function

        precalculate = data.get("precalculate", False)

        profile: Profile = {
            "name": data["name"],
            "id": data["id"],
            "cost_function": user_defined["cost_function"],
            "directions": user_defined["directions"],
            "shortest_paths": user_defined["shortest_paths"],
            "reachable": user_defined["reachable"],
            "precalculate": precalculate,
        }

        if "args" in data:
            profile["args"] = data["args"]

        return profile


def load_function_from_file(
    path: str, module_name: str, funcname: str
) -> Callable:
    renamed_module = f"{module_name}.{funcname}"

    spec = importlib.util.spec_from_file_location(renamed_module, path)
    if spec is None:
        raise Exception(f"Invalid function: {module_name}, {funcname}")
    # TODO: investigate type errors here - unclear if they matter
    module = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(module)  # type: ignore

    return getattr(module, funcname)


def load_function(
    working_path: str,
    function_path: str,
    module_name: str,
    function_name: str,
    static: Optional[Dict[str, fields.Field]] = None,
) -> Callable:
    function_path = os.path.join(working_path, function_path)
    function = load_function_from_file(
        function_path, module_name, function_name
    )
    if static is not None:
        # Apply static arguments
        function = partial(function, **static)
    return function
