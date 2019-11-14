import importlib.util
from functools import partial
import os


from marshmallow import Schema, fields, post_load

from unweaver import fields as unweaverFields


class WorkingPathRequiredError(Exception):
    # TODO: inherit from more similar exception?
    pass


class ProfileArg(Schema):
    name = fields.Str(required=True)
    type = unweaverFields.Eval(required=True)


class ProfileSchema(Schema):
    args = fields.List(fields.Nested(ProfileArg))
    cost_function = fields.Str()
    directions = fields.Str()
    name = fields.Str(required=True)
    precalculate = fields.Boolean()
    static = fields.Dict(keys=fields.Str(), values=fields.Field(), required=False)

    def get_cost_function(self, obj):
        # Is there such thing as the opposite of eval?
        pass

    def load_cost_function(self, value):
        os.path.join(self.context[path], "..", value)

    def get_directions(self, obj):
        # Is there such thing as the opposite of eval?
        pass

    def load_directions(self, value):
        os.path.join(self.context[path], "..", value)

    @post_load
    def make_profile(self, data, **kwargs):
        # TODO: investigate whether there's an elegant way to load the cost function
        # in a field type.
        if "working_path" not in self.context:
            # TODO: add useful message
            raise WorkingPathRequiredError()
        else:
            path = self.context["working_path"]

        if "cost_function" in data:
            cost_function_path = os.path.join(path, data["cost_function"])
            cost_function = load_function_from_file(
                cost_function_path, "costs", "cost_fun_generator"
            )
            if "static" in data:
                # Apply static arguments
                cost_function = partial(cost_function, **data["static"])
        else:
            cost_function = None

        if "directions" in data:
            directions_path = os.path.join(path, data["directions"])
            directions = load_function_from_file(
                directions_path, "directions", "directions"
            )
        else:
            directions = None

        precalculate = data.get("precalculate", False)

        profile = {
            **data,
            "cost_function": cost_function,
            "directions": directions,
            "precalculate": precalculate,
        }

        return profile


def load_function_from_file(path, module_name, funcname):
    filename = os.path.splitext(os.path.basename(path))[0]
    renamed_module = "{}.{}".format(module_name, filename)

    spec = importlib.util.spec_from_file_location(renamed_module, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return getattr(module, funcname)
