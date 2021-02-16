import asyncio
from inspect import isawaitable as _isawaitable

from .types import VersionType


async def maybe_coroutine(f, *args, **kwargs):
    value = f(*args, **kwargs)
    if _isawaitable(value):
        return await value
    else:
        return value


def create_task(loop, f, *args, **kwargs) -> None:
    value = f(*args, **kwargs)
    if _isawaitable(value):
        loop.create_task(value)


def with_type(value):
    value_ = value
    if isinstance(value, VersionType):
        type_ = "version"
        value_ = str(value)
    elif isinstance(value, str):
        type_ = "string"
    elif isinstance(value, int):
        type_ = "integer"
    elif isinstance(value, float):
        type_ = "float"
    elif isinstance(value, list):
        type_ = "list"
    else:
        raise ValueError(f"Invalid value: {value_!r}")

    return {"type": type_, "value": value_}
