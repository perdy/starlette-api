import asyncio
import sys
import typing
from contextlib import ExitStack
from time import sleep

import marshmallow
import pytest
import sqlalchemy
import typesystem
from faker import Faker

from flama import Flama
from flama.sqlalchemy import metadata
from flama.testclient import TestClient

if sys.version_info >= (3, 8):  # PORT: Remove when stop supporting 3.7 # pragma: no cover
    from unittest.mock import AsyncMock
else:  # pragma: no cover
    from asyncmock import AsyncMock

DATABASE_URL = "sqlite+aiosqlite://"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


class ExceptionContext:
    def __init__(self, context, exception: typing.Optional[Exception] = None):
        self.context = context
        self.exception = exception

    def __enter__(self):
        return self.context.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.context.__exit__(exc_type, exc_val, exc_tb)


@pytest.fixture(scope="function")
def exception(request):
    if request.param is None:
        context = ExceptionContext(ExitStack())
    elif isinstance(request.param, Exception):
        context = ExceptionContext(
            pytest.raises(request.param.__class__, match=getattr(request.param, "message", None)), request.param
        )
    else:
        context = ExceptionContext(pytest.raises(request.param), request.param)
    return context


@pytest.fixture(scope="function")
def puppy_schema(app):
    from flama import schemas

    if schemas.lib == typesystem:
        schema_ = typesystem.Schema(
            fields={"custom_id": typesystem.Integer(allow_null=True), "name": typesystem.String()}
        )
    elif schemas.lib == marshmallow:
        schema_ = type(
            "Puppy",
            (marshmallow.Schema,),
            {"custom_id": marshmallow.fields.Integer(allow_none=True), "name": marshmallow.fields.String()},
        )
    else:
        raise ValueError("Wrong schema lib")

    app.schema.schemas["Puppy"] = schema_
    return schema_


@pytest.fixture(scope="function")
async def puppy_model(app, client):
    table = sqlalchemy.Table(
        "puppy",
        app.sqlalchemy.metadata,
        sqlalchemy.Column("custom_id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
        sqlalchemy.Column("name", sqlalchemy.String),
    )

    async with app.sqlalchemy.engine.begin() as connection:
        await connection.run_sync(app.sqlalchemy.metadata.create_all, tables=[table])

    yield table

    async with app.sqlalchemy.engine.begin() as connection:
        await connection.run_sync(app.sqlalchemy.metadata.drop_all, tables=[table])


@pytest.fixture(scope="session")
def fake():
    return Faker()


@pytest.fixture(autouse=True)
def clear_metadata():
    metadata.clear()


@pytest.fixture(
    scope="function",
    params=[pytest.param("typesystem", id="typesystem"), pytest.param("marshmallow", id="marshmallow")],
)
def app(request):
    return Flama(
        title="Foo",
        version="0.1",
        description="Bar",
        schema="/schema/",
        docs="/docs/",
        sqlalchemy_database="sqlite+aiosqlite://",
        schema_library=request.param,
    )


@pytest.fixture(scope="function")
def client(app):
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def asgi_scope():
    return {
        "type": "http",
        "method": "GET",
        "scheme": "https",
        "path": "/",
        "root_path": "/",
        "query_string": b"",
        "headers": [],
    }


@pytest.fixture(scope="function")
def asgi_receive():
    return AsyncMock()


@pytest.fixture(scope="function")
def asgi_send():
    return AsyncMock()


def assert_recursive_contains(first, second):
    if isinstance(first, dict) and isinstance(second, dict):
        assert first.keys() <= second.keys()

        for k, v in first.items():
            assert_recursive_contains(v, second[k])
    elif isinstance(first, (list, set, tuple)) and isinstance(second, (list, set, tuple)):
        assert len(first) <= len(second)

        for i, _ in enumerate(first):
            assert_recursive_contains(first[i], second[i])
    else:
        assert first == second


def assert_read_from_file(file_path, value, max_tries=10):
    read_value = None
    i = 0
    while not read_value and i < max_tries:
        sleep(i)
        with open(file_path) as f:
            read_value = f.read()
        i += 1

    assert read_value == value
