import datetime
from unittest.mock import MagicMock, patch

import pytest

from flama.telemetry.data_structures import Error, TelemetryData


@pytest.fixture(scope="function", autouse=True)
def add_routes(app):
    @app.route("/")
    def root():
        return {"puppy": "Canna"}


@pytest.fixture(scope="function")
def asgi_scope(app, asgi_scope):
    asgi_scope["app"] = app
    return asgi_scope


class TestCaseAuthentication:
    def test_from_scope(self, asgi_scope, asgi_receive, asgi_send):
        ...


class TestCaseEndpoint:
    def test_from_scope(self, asgi_scope, asgi_receive, asgi_send):
        ...


class TestCaseRequest:
    def test_from_scope(self, asgi_scope, asgi_receive, asgi_send):
        ...


class TestCaseError:
    async def test_from_exception(self):
        now = datetime.datetime.now()
        with patch("datetime.datetime", MagicMock(now=MagicMock(return_value=now))):
            try:
                raise ValueError("Foo")
            except ValueError as e:
                error = await Error.from_exception(exception=e)

            assert error.to_dict() == {"detail": "Foo", "status_code": None, "timestamp": now.isoformat()}


class TestCaseTelemetryData:
    async def test_from_scope(self, asgi_scope, asgi_receive, asgi_send):
        data = await TelemetryData.from_scope(scope=asgi_scope, receive=asgi_receive, send=asgi_send)

        assert data.to_dict() == {}
