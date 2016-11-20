"""
HTTP server implementation on top of the aiohttp framework
"""


import asyncio
import logging
import socket
from typing import Optional
from uuid import uuid4

from aiohttp import web

from sunhead.conf import settings
# from sunhead.urls import urlpatterns
from sunhead.version import get_version
from sunhead.workers.abc import AbstractHttpServerWorker, HttpServerWorkerMixinMeta


logger = logging.getLogger(__name__)


class Server(AbstractHttpServerWorker):

    def __init__(self, fd: Optional[int] = None, host: Optional[str] = None, port: Optional[str] = None):
        self.fd = fd
        self.host = host
        self.port = port
        self._guid = str(uuid4())
        self._app = self.create_app()

        self.add_routers()
        loop = asyncio.get_event_loop()
        self.init_requirements(loop)

    @property
    def app(self) -> web.Application:
        return self._app

    @property
    def app_name(self):
        return "sunhead_http_server"

    @property
    def guid(self):
        return self._guid

    def create_app(self) -> web.Application:
        mw = self.get_middlewares()
        app = web.Application(middlewares=mw, debug=settings.DEBUG)

        if settings.USE_DEBUG_TOOLBAR:
            try:
                import aiohttp_debugtoolbar
                aiohttp_debugtoolbar.setup(app)
            except ImportError:
                logger.warning("Can't init aiohttp_debugtoolbar")
        return app

    def get_middlewares(self) -> list:
        mw = []

        if settings.DEBUG and settings.USE_DEBUG_TOOLBAR:
            try:
                from aiohttp_debugtoolbar import toolbar_middleware_factory
                mw += [toolbar_middleware_factory]
            except ImportError:
                logger.warning("Could not import 'aiohttp_debugtoolbar'. Is it installed?")

        return mw

    def print_banner(self):
        print("Powered by ☀ {}\n".format(get_version(full=True)))

    def print_config_info(self):
        logger.info("Config from '%s'", settings.SETTINGS_MODULE)
        logger.info(
            "DEBUG=%s, USE_DEBUG_TOOLBAR=%s",
            settings.DEBUG, settings.USE_DEBUG_TOOLBAR)

    def add_routers(self):
        tuple(map(lambda x: self._app.router.add_route(*x[:3]), self.get_urlpatterns()))

    def get_urlpatterns(self):
        return []

    def init_requirements(self, loop):
        pass

    def enable_reloaders(self):
        # Enable source code changes monitoring
        if settings.DEBUG and settings.DEBUG_AUTORELOAD_APP:
            import aiohttp_autoreload
            aiohttp_autoreload.start()

    def get_fd_socket(self):
        sock = None
        if settings.USE_FD_SOCKET and self.fd is not None:
            # TODO: Check socket params and better exception
            sock = socket.fromfd(self.fd, socket.AF_INET, socket.SOCK_STREAM)

        return sock

    def make_web_handler(self):
        handler = self._app.make_handler()
        return handler

    def get_server_init_kwargs(self):
        # Choose binding method
        sock = self.get_fd_socket()
        if sock is not None:
            kwargs = {
                "sock": sock,
            }
            logger.info("Serving on socket. fd={}".format(self.fd))
        else:
            kwargs = {
                "host": self.host or settings.HOST,
                "port": self.port or settings.PORT,
            }
            logger.info("Serving on address http://{host}:{port}/".format(**kwargs))
        return kwargs

    def serve(self, srv, handler, loop):
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt caught")
        finally:
            self.cleanup(srv, handler, loop)
        logger.info('Server stopped.')

    def cleanup(self, srv, handler, loop):
        loop.run_until_complete(handler.finish_connections(1.0))
        srv.close()
        loop.run_until_complete(srv.wait_closed())
        loop.run_until_complete(self._app.finish())

    @property
    def wsgi_app(self):
        """
        Expose WSGI application to different servers, which can deal with aiohttp workers. Gunicorn does.

        Example usage::

            gunicorn --bind localhost:8080 --worker-class aiohttp.worker.GunicornWebWorker -w 4 your_pkg:app

        RPSes are growing well, but be careful with race conditions.
        """
        return self._app

    def run(self):

        # Information
        self.print_banner()
        self.print_config_info()

        # Init stuff
        loop = asyncio.get_event_loop()
        self.enable_reloaders()

        # Define serving method
        kwargs = self.get_server_init_kwargs()
        handler = self.make_web_handler()

        # Start server
        logger.info("Server GUID=%s", self.guid)
        f = loop.create_server(handler, **kwargs)
        srv = loop.run_until_complete(f)

        # Serve forever
        self.serve(srv, handler, loop)
        loop.close()


class BaseServerMixin(metaclass=HttpServerWorkerMixinMeta):
    pass
