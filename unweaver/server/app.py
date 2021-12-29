from types import TracebackType
from typing import (
    Any,
    ByteString,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Text,
    Tuple,
    Type,
    TypedDict,
    Union,
)

from flask import Flask, Response, jsonify
from werkzeug.exceptions import HTTPException


# Copied from flask-stub, had issues importing _ViewFuncReturnType
_ExcInfo = Tuple[
    Optional[Type[BaseException]],
    Optional[BaseException],
    Optional[TracebackType],
]
_StartResponse = Callable[
    [str, List[Tuple[str, str]], Optional[_ExcInfo]], Callable[[bytes], Any]
]
_WSGICallable = Callable[[Dict[Text, Any], _StartResponse], Iterable[bytes]]
_Status = Union[str, int]
_Headers = Union[Dict[Any, Any], List[Tuple[Any, Any]]]
_Body = Union[Text, ByteString, Dict[Text, Any], Response, _WSGICallable]
_ViewFuncReturnType = Union[
    _Body,
    Tuple[_Body, _Status, _Headers],
    Tuple[_Body, _Status],
    Tuple[_Body, _Headers],
]


# Have to extend HTTPException to annotate extra data added by Webargs
# TODO: this is an incomplete type annotation (note the use of Any)
class WebargsHTTPExceptionData(TypedDict):
    headers: Optional[Union[Dict[Any, Any], List[Tuple[Any, Any]]]]
    messages: Optional[Dict[Text, Any]]


class WebargsHTTPException(HTTPException):
    data: WebargsHTTPExceptionData


def create_app() -> Flask:
    app = Flask(__name__)

    # TODO: handle 400 distinctly?
    @app.errorhandler(422)
    def handle_error(err: WebargsHTTPException) -> _ViewFuncReturnType:
        if err.data is None:
            return "Unknown validation error.", err.code
        headers = err.data.get("headers", None)
        messages = err.data.get("messages", ["Invalid request."])
        body: str = jsonify({"errors": messages})
        code: int = getattr(err, "code", 422)
        if headers:
            return body, code, headers
        else:
            return body, code

    return app
