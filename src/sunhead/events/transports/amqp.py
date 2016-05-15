"""
Use this module members to connect to RabbitMQ instance.
"""

import asyncio
import logging
from fnmatch import fnmatch
from typing import AnyStr, Sequence, Optional
from uuid import uuid4

import aioamqp

from sunhead.events import exceptions
from sunhead.events.abc import AbstractTransport, AbstractSubscriber
from sunhead.events.types import Transferrable
from sunhead.serializers import JSONSerializer

logger = logging.getLogger(__name__)


# TODO: Better implementation of single connection, routing & internal pub/sub
# Note: Now it is possible to call ``consume_queue`` multiple times and get several
# bindings to routing keys and multiple queues. Think over this thing.

class AMQPClient(AbstractTransport):
    """
    Handy implementation of the asynchronous AMQP client.
    Useful for building both publishers and consumers.
    """

    DEFAULT_EXCHANGE_NAME = "default_exchange"
    DEFAULT_EXCHANGE_TYPE = "topic"

    def __init__(
            self,
            connection_parameters: dict,
            exchange_name: str = DEFAULT_EXCHANGE_NAME,
            exchange_type: str = DEFAULT_EXCHANGE_TYPE,
            global_qos: Optional[int] = None,
            **kwargs):

        """
        There must be at least these members of the connection_parameters dict::

            "connection_parameters": {
                "login": "",
                "password": "",
                "host": "",
                "port": "",
                "virtualhost": "",
            },


        :param connection_parameters: Dict with connection parameters. See above for its format.
        :return: EventsQueueClient instance.
        """

        # Can not pass empty password when connecting. Must remove the field completely.
        if not connection_parameters.get("password", ""):
            connection_parameters.pop("password", None)

        self._connection_parameters = connection_parameters or {}
        self._transport = None
        self._protocol = None
        self._channel = None
        self._exchange_name = exchange_name
        self._exchange_type = exchange_type
        self._global_qos = global_qos
        self._serializer = self._get_serializer()
        self._is_connecting = False
        self._connection_guid = str(uuid4())
        self._known_queues = {}
        self._routing = {}

    def _get_serializer(self):
        # TODO: Make serializer configurable here
        return JSONSerializer()

    @property
    def connected(self):
        return self._channel is not None and self._channel.is_open

    @property
    def is_connecting(self) -> bool:
        return self._is_connecting

    async def connect(self):
        """
        Create new asynchronous connection to the RabbitMQ instance.
        This will connect, declare exchange and bind itself to the configured queue.

        After that, client is ready to publish or consume messages.

        :return: Does not return anything.
        """
        if self.connected or self.is_connecting:
            return

        self._is_connecting = True
        try:
            logger.info("Connecting to RabbitMQ...")
            self._transport, self._protocol = await aioamqp.connect(**self._connection_parameters)

            logger.info("Getting channel...")
            self._channel = await self._protocol.channel()

            if self._global_qos is not None:
                logger.info("Setting prefetch count on connection (%s)", self._global_qos)
                await self._channel.basic_qos(0, self._global_qos, 1)

            logger.info("Connecting to exchange '%s (%s)'", self._exchange_name, self._exchange_type)
            await self._channel.exchange(self._exchange_name, self._exchange_type)

        except (aioamqp.AmqpClosedConnection, Exception):
            logger.error("Error initializing RabbitMQ connection", exc_info=True)
            self._is_connecting = False
            raise exceptions.StreamConnectionError

        self._is_connecting = False

    async def close(self):
        self._protocol.stop()
        await self._channel.close()

    async def publish(self, data: Transferrable, topic: AnyStr) -> None:
        if not self.connected:
            logger.warning("Attempted to send message while not connected")
            return

        body = self._serializer.serialize(data)

        await self._channel.publish(
            body,
            exchange_name=self._exchange_name,
            routing_key=topic
        )
        # Uncomment for debugging
        # logger.debug("Published message to AMQP exchange=%s, topic=%s", self._exchange_name, topic)

    async def consume_queue(self, subscriber: AbstractSubscriber) -> None:

        """
        Subscribe to the queue consuming.

        :param subscriber:
        :return:
        """

        queue_name = subscriber.name
        topics = subscriber.requested_topics

        if queue_name in self._known_queues:
            raise exceptions.ConsumerError("Queue '%s' already being consumed" % queue_name)

        await self._declare_queue(queue_name)

        # TODO: There is a lot of room to improvement here. Figure out routing done the right way
        for key in topics:
            self._routing.setdefault(key, set())
            if subscriber in self._routing[key]:
                logger.warning("Subscriber '%s' already receiving routing_key '%s'", subscriber, key)
                break
            await self._bind_key_to_queue(key, queue_name)
            self._routing[key].add(subscriber)

        logger.info("Consuming queue '%s'", queue_name)
        await asyncio.wait_for(
            self._channel.basic_consume(callback=self._on_message, queue_name=queue_name),
            timeout=10
        )
        self._add_to_known_queue(queue_name)

    async def _declare_queue(self, queue_name: AnyStr) -> None:
        logger.info("Declaring queue...")
        queue_declaration = await self._channel.queue_declare(queue_name)
        queue_name = queue_declaration.get("queue")
        logger.info("Declared queue '%s'", queue_name)

    async def _bind_key_to_queue(self, routing_key: AnyStr, queue_name: AnyStr) -> None:
        """
        Bind to queue with specified routing key.

        :param routing_key: Routing key to bind with.
        :param queue_name: Name of the queue
        :return: Does not return anything
        """
        logger.info("Binding key='%s'", routing_key)

        result = await self._channel.queue_bind(
            exchange_name=self._exchange_name,
            queue_name=queue_name,
            routing_key=routing_key,
        )
        return result

    async def _on_message(self, channel, body, envelope, properties) -> None:
        """
        Fires up when message is received by this consumer.

        :param channel: Channel, through which message is received
        :param body: Body of the message (serialized).
        :param envelope: Envelope object with message meta
        :type envelope: aioamqp.Envelope
        :param properties: Properties of the message
        :return: Coroutine object with result of message handling operation
        """

        subscribers = self._get_subscribers(envelope.routing_key)
        if not subscribers:
            logger.debug("No route for message with key '%s'", envelope.routing_key)
            return

        body = self._serializer.deserialize(body)

        for subscriber in subscribers:
            # Check later if ensure_future can be applied here
            await subscriber.on_message(body, envelope.routing_key)

        await self._channel.basic_client_ack(envelope.delivery_tag)

    def _get_subscribers(self, incoming_routing_key: AnyStr) -> Sequence[AbstractSubscriber]:
        for key, subscribers in self._routing.items():
            if fnmatch(incoming_routing_key, key):
                return subscribers
        return tuple()

    def _add_to_known_queue(self, queue_name: AnyStr) -> None:
        self._known_queues[queue_name] = {
            "bound_keys": set(),
        }
