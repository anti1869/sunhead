"""
Base worker with Stream connection. No subscribers defined
"""

import asyncio
import logging
from uuid import uuid4

from sunhead.conf import settings
from sunhead.events.stream import init_stream_from_settings
from sunhead.workers.abc import AbstractStreamWorker


logger = logging.getLogger(__name__)


class StreamConnectionMixin(object):

    CFG_SETTINGS_KEY = "STREAM"

    def __init__(self, *args, **kwargs):
        getattr(super(), "__init__")(*args, **kwargs)
        self._stream = None

    @property
    def stream(self):
        return self._stream

    async def connect_to_stream(self):
        self._stream = await init_stream_from_settings(getattr(settings, self.CFG_SETTINGS_KEY, {}))


class StreamWorker(StreamConnectionMixin, AbstractStreamWorker):

    def __init__(self):
        super().__init__()
        self._guid = str(uuid4())

    @property
    def app_name(self):
        return "sunhead.stream_worker"

    @property
    def guid(self):
        return self._guid

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.connect_to_stream())
        loop.run_until_complete(self.add_subscribers())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt caught")
        finally:
            loop.stop()

        logger.info("Worker stopped.")

    async def add_subscribers(self):
        pass
