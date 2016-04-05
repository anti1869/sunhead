"""
Abstract and bases for building messaging stuff.
"""

from abc import ABCMeta, abstractmethod, ABC, abstractproperty
from typing import AnyStr, Sequence

from sunhead.events.types import Transferrable, Serialized


class SingleConnectionMeta(ABC):
    """
    Ensures that connection class is made once and for all.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class AbstractSubscriber(object, metaclass=ABCMeta):

    @abstractmethod
    async def on_message(self, data: Transferrable, topic: AnyStr):
        pass

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def requested_topics(self):
        pass


class AbstractTransport(SingleConnectionMeta):

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    @property
    @abstractmethod
    def connected(self) -> bool:
        pass

    @property
    @abstractmethod
    def is_connecting(self) -> bool:
        pass

    @abstractmethod
    async def publish(self, data: Transferrable, topic: AnyStr) -> None:
        pass

    @abstractmethod
    async def consume_queue(self, subscriber: AbstractSubscriber) -> None:
        pass


class AbstractSerializer(object, metaclass=ABCMeta):

    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @property
    @abstractmethod
    def graceful(self):
        pass

    @graceful.setter
    @abstractmethod
    def graceful(self, value):
        pass

    @abstractmethod
    def set_defaults(self, serialized, unserialized):
        pass

    @abstractmethod
    def serialize(self, data: Transferrable) -> Serialized:
        pass

    @abstractmethod
    def deserialize(self, msg: Serialized) -> Transferrable:
        pass