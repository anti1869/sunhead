"""
Stream is a flow of messages in one particular bus. It could be RabbitMQ exchange, for example.

You can subscribe to messages from the Stream, organize distributed dequeuing or publish data there.
"""

import asyncio
from importlib import import_module
import logging
from typing import Sequence, AnyStr

from sunhead.events.abc import AbstractSubscriber, AbstractTransport, SingleConnectionMeta
from sunhead.events.exceptions import StreamConnectionError
from sunhead.periodical import crontab
from sunhead.events.types import Transferrable


logger = logging.getLogger(__name__)


DEFAULT_TRANSPORT = "brandt.events.transports.amqp.AMQPClient"


__all__ = ("Stream", "get_stream", "init_stream_from_settings")


class Stream(object):

    CONNECTION_CHECK_SECS = 20

    def __init__(self, transport=DEFAULT_TRANSPORT, **transport_init_kwargs):
        self._transport_name = transport
        self._transport_class = self._get_transport_class(self._transport_name)
        self._transport = self._init_transport(self._transport_class, transport_init_kwargs)
        self._reconnecter = crontab(
            "* * * * * */{}".format(self.CONNECTION_CHECK_SECS), func=self._reconnect, start=False)
        self._reconnect_attempts = 0

    def _get_transport_class(self, transport_name) -> type:
        module_name, class_name = transport_name.rsplit(".", 1)

        try:
            transport_module = import_module(module_name)
        except ImportError:
            logger.error("Can't import transport with name `%s`", module_name)
            raise

        try:
            transport_class = getattr(transport_module, class_name)
        except AttributeError:
            logger.error("Can't get transport class `%s` from `%s`", class_name, module_name)
            raise

        return transport_class

    def _init_transport(self, transport_class, transport_init_kwargs) -> AbstractTransport:
        return transport_class(**transport_init_kwargs)

    async def connect(self):
        if self.connected or self._transport.is_connecting:
            return

        try:
            await self._transport.connect()
        except StreamConnectionError:
            logger.error("Can't initialize Stream connection", exc_info=True)
        finally:
            self._reconnecter.start()

    async def _reconnect(self):
        logger.debug("Checking Stream connection is alive")
        if self.connected or self._transport.is_connecting:
            return

        logger.info("Trying to reconnect Events Stream")
        self._reconnect_attempts += 1
        try:
            await self.connect()
        except StreamConnectionError:
            logger.info("Unsuccessfull attempt to reconnect #%s", self._reconnect_attempts)
        else:
            self._reconnect_attempts = 0

    @property
    def connected(self) -> bool:
        return self._transport.connected

    async def publish(self, data: Transferrable, topics: Sequence[AnyStr]) -> None:
        for topic in topics:
            # asyncio.ensure_future(self._transport.publish(data, topic))
            # Here's the deal. If multiple ``publish`` occurs immediately in a cycle,
            # ensure_future will only happen after all this cycle completes, or there
            # will be possibility window. So maybe better to use await here?
            await self._transport.publish(data, topic)

    async def subscribe(self, subscriber: AbstractSubscriber, topics: Sequence[AnyStr]) -> None:
        raise NotImplementedError

    async def dequeue(self, subscriber: AbstractSubscriber) -> None:
        await self._transport.consume_queue(subscriber)

    async def close(self):
        logger.info("Closing Stream")
        await self._transport.close()


class StreamStorage(dict):

    DEFAULT_KEY = "default"

    def get_default(self) -> Stream:
        result = self.get(self.DEFAULT_KEY, None)
        return result

    def push(self, key: str, value: Stream):
        if not len(self):
            self[self.DEFAULT_KEY] = value
        self[key] = value


_stream_storage = StreamStorage()


async def init_stream_from_settings(cfg: dict) -> Stream:
    """
    Shortcut to create Stream from configured settings.

    Will definitely fail if there is no meaningful configuration provided. Example of such is::

        {
            "streams": {
                "rabbitmq": {
                    "transport": "sunhead.events.transports.amqp.AMQPClient",
                    "connection_parameters": {
                        "login": "guest",
                        "password": "",
                        "host": "localhost",
                        "port": 5672,
                        "virtualhost": "video",
                    },
                    "exchange_name": "video_bus",
                    "exchange_type": "topic",
                    "global_qos": None,
                },
                "kafka": {},
            },
            "active_stream": "rabbitmq",
        }

    :return: Instantiated Stream object.
    """
    cfg_name = cfg["active_stream"]
    stream_init_kwargs = cfg["streams"][cfg_name]
    stream = Stream(**stream_init_kwargs)
    await stream.connect()
    _stream_storage.push(cfg_name, stream)
    return stream


def get_stream(name: str = None) -> Stream:
    stream = _stream_storage.get(name) if name else _stream_storage.get_default()
    return stream
