from marshmallow import fields, validate


class Eval(fields.Str):
    def _serialize(self, value, attr, obj):
        pass

    def _deserialize(self, value, attr, data):
        return eval(value)
