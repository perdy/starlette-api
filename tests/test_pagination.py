import marshmallow
import pytest
from starlette.testclient import TestClient

from flama import pagination
from flama.applications import Flama


class OutputSchema(marshmallow.Schema):
    value = marshmallow.fields.Integer()


class TestPageNumberResponse:
    @pytest.fixture
    def app(self):
        app_ = Flama(title="Foo", version="0.1", description="Bar", schema="/schema/")

        @app_.route("/page-number/", methods=["GET"])
        @pagination.page_number
        def page_number(**kwargs) -> OutputSchema(many=True):
            return [{"value": i} for i in range(25)]

        return app_

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_invalid_view(self, app):
        with pytest.raises(TypeError, match=r"Paginated views must define \*\*kwargs param"):

            @pagination.page_number
            def invalid():
                ...

    def test_pagination_schema_parameters(self, app):
        schema = app.schema["paths"]["/page-number/"]["get"]
        parameters = schema.get("parameters", {})

        assert parameters == [
            {"name": "page", "in": "query", "required": False, "schema": {"type": "integer", "nullable": True}},
            {"name": "page_size", "in": "query", "required": False, "schema": {"type": "integer", "nullable": True}},
            {"name": "count", "in": "query", "required": False, "schema": {"type": "boolean", "default": True}},
        ]

    def test_pagination_schema_return(self, app):
        response_schema = app.schema["paths"]["/page-number/"]["get"]["responses"]["200"]
        component_schema = app.schema["components"]["schemas"]["PageNumberPaginatedOutputSchema"]

        assert component_schema == {
            "properties": {
                "data": {"items": {"$ref": "#/components/schemas/Output"}, "type": "array"},
                "meta": {"$ref": "#/components/schemas/PageNumberMeta"},
            },
            "type": "object",
        }

        assert response_schema == {
            "description": "Description not provided.",
            "content": {
                "application/json": {"schema": {"$ref": "#/components/schemas/PageNumberPaginatedOutputSchema"}},
            },
        }

    def test_async_function(self, app, client):
        @app.route("/page-number-async/", methods=["GET"])
        @pagination.page_number
        async def page_number_async(**kwargs) -> OutputSchema(many=True):
            return [{"value": i} for i in range(25)]

        response = client.get("/page-number-async/")
        assert response.status_code == 200, response.json()
        assert response.json() == {
            "meta": {"page": 1, "page_size": 10, "count": 25},
            "data": [{"value": i} for i in range(10)],
        }

    def test_default_params(self, client):
        response = client.get("/page-number/")
        assert response.status_code == 200
        assert response.json() == {
            "meta": {"page": 1, "page_size": 10, "count": 25},
            "data": [{"value": i} for i in range(10)],
        }

    def test_default_page_explicit_size(self, client):
        response = client.get("/page-number/", params={"page_size": 5})
        assert response.status_code == 200
        assert response.json() == {
            "meta": {"page": 1, "page_size": 5, "count": 25},
            "data": [{"value": i} for i in range(5)],
        }

    def test_default_size_explicit_page(self, client):
        response = client.get("/page-number/", params={"page": 2})
        assert response.status_code == 200
        assert response.json() == {
            "meta": {"page": 2, "page_size": 10, "count": 25},
            "data": [{"value": i} for i in range(10, 20)],
        }

    def test_explicit_params(self, client):
        response = client.get("/page-number/", params={"page": 4, "page_size": 5})
        assert response.status_code == 200
        assert response.json() == {
            "meta": {"page": 4, "page_size": 5, "count": 25},
            "data": [{"value": i} for i in range(15, 20)],
        }

    def test_no_count(self, client):
        response = client.get("/page-number/", params={"count": False})
        assert response.status_code == 200
        assert response.json() == {
            "meta": {"page": 1, "page_size": 10, "count": None},
            "data": [{"value": i} for i in range(10)],
        }


class TestLimitOffsetResponse:
    @pytest.fixture(scope="class")
    def app(self):
        app_ = Flama(title="Foo", version="0.1", description="Bar", schema="/schema/")

        @app_.route("/limit-offset/", methods=["GET"])
        @pagination.limit_offset
        def limit_offset(**kwargs) -> OutputSchema(many=True):
            return [{"value": i} for i in range(25)]

        return app_

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_invalid_view(self, app):
        with pytest.raises(TypeError, match=r"Paginated views must define \*\*kwargs param"):

            @pagination.limit_offset
            def invalid():
                ...

    def test_pagination_schema_parameters(self, app):
        schema = app.schema["paths"]["/limit-offset/"]["get"]
        parameters = schema.get("parameters", {})

        assert parameters == [
            {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer", "nullable": True}},
            {"name": "offset", "in": "query", "required": False, "schema": {"type": "integer", "nullable": True}},
            {"name": "count", "in": "query", "required": False, "schema": {"type": "boolean", "default": True}},
        ]

    def test_pagination_schema_return(self, app):
        response_schema = app.schema["paths"]["/limit-offset/"]["get"]["responses"]["200"]
        component_schema = app.schema["components"]["schemas"]["LimitOffsetPaginatedOutputSchema"]

        assert component_schema == {
            "type": "object",
            "properties": {
                "data": {"items": {"$ref": "#/components/schemas/Output"}, "type": "array"},
                "meta": {"$ref": "#/components/schemas/LimitOffsetMeta"},
            },
        }

        assert response_schema == {
            "description": "Description not provided.",
            "content": {
                "application/json": {"schema": {"$ref": "#/components/schemas/LimitOffsetPaginatedOutputSchema"}}
            },
        }

    def test_async_function(self, app, client):
        @app.route("/limit-offset-async/", methods=["GET"])
        @pagination.limit_offset
        async def limit_offset_async(**kwargs) -> OutputSchema(many=True):
            return [{"value": i} for i in range(25)]

        response = client.get("/limit-offset-async/")
        assert response.status_code == 200, response.json()
        assert response.json() == {
            "meta": {"limit": 10, "offset": 0, "count": 25},
            "data": [{"value": i} for i in range(10)],
        }

    def test_default_params(self, client):
        response = client.get("/limit-offset/")
        assert response.status_code == 200, response.json()
        assert response.json() == {
            "meta": {"limit": 10, "offset": 0, "count": 25},
            "data": [{"value": i} for i in range(10)],
        }

    def test_default_offset_explicit_limit(self, client):
        response = client.get("/limit-offset/", params={"limit": 5})
        assert response.status_code == 200
        assert response.json() == {
            "meta": {"limit": 5, "offset": 0, "count": 25},
            "data": [{"value": i} for i in range(5)],
        }

    def test_default_limit_explicit_offset(self, client):
        response = client.get("/limit-offset/", params={"offset": 5})
        assert response.status_code == 200
        assert response.json() == {
            "meta": {"limit": 10, "offset": 5, "count": 25},
            "data": [{"value": i} for i in range(5, 15)],
        }

    def test_explicit_params(self, client):
        response = client.get("/limit-offset/", params={"offset": 5, "limit": 20})
        assert response.status_code == 200
        assert response.json() == {
            "meta": {"limit": 20, "offset": 5, "count": 25},
            "data": [{"value": i} for i in range(5, 25)],
        }

    def test_no_count(self, client):
        response = client.get("/limit-offset/", params={"count": False})
        assert response.status_code == 200
        assert response.json() == {
            "meta": {"limit": 10, "offset": 0, "count": None},
            "data": [{"value": i} for i in range(10)],
        }
