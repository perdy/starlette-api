import typing

from flama.modules import Module

try:
    import sqlalchemy
    from sqlalchemy.ext.asyncio import create_async_engine
except Exception:  # pragma: no cover
    sqlalchemy = None  # type: ignore

if typing.TYPE_CHECKING:
    from flama import Flama


class DatabaseModule(Module):
    name = "database"

    def __init__(self, app: "Flama", database: str = None, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        if database:  # pragma: no cover
            assert sqlalchemy is not None, "sqlalchemy[asyncio] must be installed to use DatabaseModule"
            self.engine = create_async_engine(database)
            self.metadata = sqlalchemy.MetaData()
