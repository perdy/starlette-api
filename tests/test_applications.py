from unittest.mock import MagicMock

import pytest

from flama import Component, Flama, Module, Mount, Route, Router
from flama.applications import DEFAULT_MODULES
from flama.components import Components
from flama.injection import Injector


class TestCaseFlama:
    @pytest.fixture(scope="function")
    def component_mock(self):
        return MagicMock(spec=Component)

    @pytest.fixture(scope="function")
    def module_mock(self):
        class Foo(Module):
            name = "foo"

        return Foo

    def test_injector(self, app):
        assert isinstance(app.injector, Injector)

    def test_components(self, app):
        assert isinstance(app.components, Components)
        assert app.components == []

    def test_recursion(self, component_mock, module_mock):
        root_app = Flama(schema=None, docs=None)
        root_app.add_get("/foo", lambda: {})

        assert len(root_app.router.routes) == 1
        assert root_app.router.main_app == root_app
        assert root_app.components == []
        assert root_app.modules == DEFAULT_MODULES

        leaf_app = Flama(schema=None, docs=None, components=[component_mock], modules=[module_mock])
        leaf_app.add_get("/bar", lambda: {})

        assert len(leaf_app.router.routes) == 1
        assert leaf_app.router.main_app == leaf_app
        assert leaf_app.components == [component_mock]
        assert leaf_app.modules == [*DEFAULT_MODULES, module_mock]

        root_app.mount("/app", app=leaf_app)

        assert len(root_app.router.routes) == 2
        # Check mount is initialized
        assert isinstance(root_app.routes[1], Mount)
        mount_route = root_app.router.routes[1]
        assert mount_route.path == "/app"
        # Check router is created and initialized
        assert isinstance(mount_route.app, Flama)
        mount_app = mount_route.app
        assert isinstance(mount_app.app, Router)
        mount_router = mount_app.app
        # Check main_app is propagated
        assert mount_router.main_app == root_app
        # Check components are collected across the entire tree
        assert mount_router.components == [component_mock]
        assert root_app.components == [component_mock]
        # Check modules are isolated for each app
        assert mount_app.modules == [*DEFAULT_MODULES, module_mock]
        assert root_app.modules == DEFAULT_MODULES

    def test_declarative_recursion(self, component_mock, module_mock):
        leaf_routes = [Route("/bar", lambda: {})]
        leaf_app = Flama(routes=leaf_routes, schema=None, docs=None, components=[component_mock], modules=[module_mock])
        root_routes = [Route("/foo", lambda: {}), Mount("/app", app=leaf_app)]
        root_app = Flama(routes=root_routes, schema=None, docs=None)

        assert len(root_app.router.routes) == 2
        # Check mount is initialized
        assert isinstance(root_app.routes[1], Mount)
        mount_route = root_app.router.routes[1]
        assert mount_route.path == "/app"
        # Check router is created and initialized
        assert isinstance(mount_route.app, Flama)
        mount_app = mount_route.app
        assert isinstance(mount_app.app, Router)
        mount_router = mount_app.app
        # Check main_app is propagated
        assert mount_router.main_app == root_app
        # Check components are collected across the entire tree
        assert mount_router.components == [component_mock]
        assert root_app.components == [component_mock]
        # Check modules are isolated for each app
        assert mount_app.modules == [*DEFAULT_MODULES, module_mock]
        assert root_app.modules == DEFAULT_MODULES
