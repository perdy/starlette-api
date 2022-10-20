import typing as t

import starlette.websockets

from flama import concurrency, exceptions, http, types, websockets

__all__ = ["HTTPEndpoint", "WebSocketEndpoint"]


class HTTPEndpoint:
    def __init__(self, scope: "types.Scope", receive: "types.Receive", send: "types.Send") -> None:
        """An HTTP endpoint.

        :param scope: ASGI scope.
        :param receive: ASGI receive function.
        :param send: ASGI send function.
        """
        assert scope["type"] == "http"
        app = scope["app"]
        route, route_scope = app.router.get_route_from_scope(scope)
        self.state = {
            "scope": scope,
            "receive": receive,
            "send": send,
            "exc": None,
            "app": app,
            "path_params": route_scope["path_params"],
            "route": route,
            "request": http.Request(scope, receive=receive),
        }

    def __await__(self) -> t.Generator:
        return self.dispatch().__await__()

    @classmethod
    def allowed_methods(cls) -> t.Set[str]:
        """The list of allowed methods by this endpoint.

        :return: List of allowed methods.
        """
        return {method for method in http.Method.__members__.keys() if getattr(cls, method.lower(), None) is not None}

    @property
    def handler(self) -> t.Callable:
        """The handler used for dispatching this request.

        :return: Handler.
        """
        handler_name = "get" if self.state["request"].method == "HEAD" else self.state["request"].method.lower()
        h: t.Callable = getattr(self, handler_name)
        return h

    async def dispatch(self) -> None:
        """Dispatch a request."""
        app = self.state["app"]
        handler = await app.injector.inject(self.handler, self.state)
        return await concurrency.run(handler)


class WebSocketEndpoint:
    encoding: t.Optional[types.Encoding] = None

    def __init__(self, scope: "types.Scope", receive: "types.Receive", send: "types.Send") -> None:
        """A websocket endpoint.

        :param scope: ASGI scope.
        :param receive: ASGI receive function.
        :param send: ASGI send function.
        """
        assert scope["type"] == "websocket"
        app = scope["app"]
        route, route_scope = app.router.get_route_from_scope(scope)
        self.state = {
            "scope": scope,
            "receive": receive,
            "send": send,
            "exc": None,
            "app": app,
            "path_params": route_scope["path_params"],
            "route": route,
            "websocket": websockets.WebSocket(scope, receive, send),
            "websocket_encoding": self.encoding,
            "websocket_code": None,
            "websocket_message": None,
        }

    def __await__(self) -> t.Generator:
        return self.dispatch().__await__()

    async def dispatch(self) -> None:
        """Dispatch a request."""
        app = self.state["app"]
        websocket = self.state["websocket"]

        on_connect = await app.injector.inject(self.on_connect, self.state)
        await on_connect()

        try:
            self.state["websocket_message"] = await websocket.receive()

            while websocket.is_connected:
                on_receive = await app.injector.inject(self.on_receive, self.state)
                await on_receive()
                self.state["websocket_message"] = await websocket.receive()

            self.state["websocket_code"] = types.Code(int(self.state["websocket_message"].get("code", 1000)))
        except starlette.websockets.WebSocketDisconnect as e:
            self.state["websocket_code"] = types.Code(e.code)
            raise exceptions.WebSocketException(e.code, e.reason) from None
        except exceptions.WebSocketException as e:
            self.state["websocket_code"] = types.Code(e.code)
            raise e from None
        except Exception as e:
            self.state["websocket_code"] = types.Code(1011)
            raise e from None
        finally:
            on_disconnect = await app.injector.inject(self.on_disconnect, self.state)
            await on_disconnect()

    async def on_connect(self, websocket: websockets.WebSocket) -> None:
        """Override to handle an incoming websocket connection.

        :param websocket: Websocket.
        """
        await websocket.accept()

    async def on_receive(self, websocket: websockets.WebSocket, data: types.Data) -> None:
        """Override to handle an incoming websocket message.

        :param websocket: Websocket.
        :param data: Received data.
        """
        ...

    async def on_disconnect(self, websocket: websockets.WebSocket, websocket_code: types.Code) -> None:
        """Override to handle a disconnecting websocket.

        :param websocket: Websocket.
        :param websocket_code: Websocket closing code.
        """
        await websocket.close(websocket_code)
