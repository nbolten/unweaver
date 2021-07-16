from typing import Any, Mapping, Optional

# validate has to be imported for eval to work correctly with fields
from marshmallow import fields, validate

# TODO: Nail down type annotations


class Eval(fields.Str):
    def _serialize(
        self, value: Any, attr: str, obj: Any, **kwargs: Any
    ) -> None:
        pass

    def _deserialize(
        self,
        value: Any,
        attr: Optional[str],
        data: Optional[Mapping[str, Any]],
        **kwargs: Any
    ) -> Any:
        return eval(value)
