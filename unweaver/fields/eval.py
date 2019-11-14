from marshmallow import fields, validate


class Eval(fields.Str):
    def _serialize(self, value, attr, obj, **kwargs):
        pass

    def _deserialize(self, value, attr, data, **kwargs):
        return eval(value)
