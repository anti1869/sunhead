"""
Abstract base classes for construction asynchronous workers.
"""

from abc import ABCMeta, abstractmethod
from typing import Sequence, Tuple

from aiohttp.web import Application


class AbstractWorker(metaclass=ABCMeta):
    """
    This base class provides most basic functionality for the worker.
    """

    @property
    @abstractmethod
    def app_name(self) -> str:
        pass

    @property
    @abstractmethod
    def guid(self) -> str:
        pass

    @abstractmethod
    def run(self) -> None:
        pass


class AbstractStreamWorker(AbstractWorker):
    """
    Base class for the worker, who operates on a stream of events.
    """

    @property
    @abstractmethod
    def stream(self):
        pass

    @abstractmethod
    async def connect_to_stream(self):
        pass

    @abstractmethod
    async def add_subscribers(self):
        pass


class AbstractHttpServerWorker(AbstractWorker):
    """
    Base for the HTTP server implementation on top of aiohttp.
    """

    @property
    @abstractmethod
    def app(self) -> Application:
        pass

    @abstractmethod
    def create_app(self) -> Application:
        pass

    @abstractmethod
    def get_middlewares(self) -> list:
        pass

    @abstractmethod
    def init_requirements(self, loop) -> None:
        pass

    @abstractmethod
    def add_routers(self) -> None:
        pass

    @abstractmethod
    def get_urlpatterns(self) -> Sequence[Tuple]:
        pass

    @property
    @abstractmethod
    def wsgi_app(self) -> Application:
        pass

    @abstractmethod
    def serve(self, srv, handler, loop) -> None:
        pass


class HttpServerWorkerMixinMeta(ABCMeta):
    """
    Ensures that mixin only applies to HttpServerWorker concrete classes.
    """

    def __call__(cls, *args, **kwargs):
        # TODO: Figure out how to properly add special methods and checks here for accessing Server class
        # if AbstractHttpServerWorker not in cls.__bases__:
        #     raise TypeError(
        #         "'HttpServerWorkerMixinMeta' can only be applied "
        #         "to 'AbstractHttpServerWorker' implementation classes"
        #     )
        return super().__call__(*args, **kwargs)
