import importlib.util
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
    name = fields.Str(required=True)
    args = fields.List(fields.Nested(ProfileArg))
    cost_function = fields.Str()
    directions = fields.Str()

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
    def make_profile(self, data):
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
        else:
            cost_function = None

        if "directions" in data:
            directions_path = os.path.join(path, data["directions"])
            directions = load_function_from_file(
                directions_path, "directions", "directions"
            )
        else:
            directions = None

        profile_args = {
            **data,
            "cost_function": cost_function,
            "directions": directions,
        }

        return Profile(**profile_args)


class Profile:
    def __init__(self, name, args=None, cost_function=None, directions=None):
        self.name = name
        if args is not None:
            self.args = args
        if cost_function is not None:
            self.cost_function_generator = cost_function
        if directions is not None:
            self.directions = directions


def load_function_from_file(path, module_name, funcname):
    filename = os.path.splitext(os.path.basename(path))[0]
    renamed_module = "{}.{}".format(module_name, filename)

    spec = importlib.util.spec_from_file_location(renamed_module, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return getattr(module, funcname)
