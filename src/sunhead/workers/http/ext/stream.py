"""
Connect http server to the Stream to send and receive messages.
"""

import asyncio

from sunhead.workers.abc import AbstractHttpServerWorker
from sunhead.workers.http.server import BaseServerMixin
from sunhead.workers.stream import StreamConnectionMixin


class ServerStreamConnection(StreamConnectionMixin, BaseServerMixin):

    # TODO: Can't set BaseServerMixin as base object here and receive correct MRO in Server subclass
    @property
    def _server_instance(self) -> AbstractHttpServerWorker:
        """Access the server instance object. Also makes PyCharm aware of the parent class"""
        return self

    def init_requirements(self, loop: asyncio.AbstractEventLoop):
        getattr(super(), "init_requirements")(loop)
        loop.run_until_complete(
            self.connect_to_stream()
        )

        # Save to app object to be accessible in request handlers
        self._server_instance.app.stream = self._stream

    def cleanup(self, srv, handler, loop):
        loop.run_until_complete(getattr(self._server_instance.app, "stream").close())
        getattr(super(), "cleanup")(srv, handler, loop)
