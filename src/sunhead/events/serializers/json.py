"""
JSON message body serializer
"""

import logging

try:
    import simplejson as json
except ImportError:
    import json

from sunhead.events.abc import AbstractSerializer
from sunhead.events.exceptions import SerializationError
from sunhead.events.types import Transferrable, Serialized


logger = logging.getLogger(__name__)


class JSONSerializer(AbstractSerializer):

    _DEF_SERIALIZED_DEFAULT = "{}"
    _DEF_DESERIALIZED_DEFAULT = {}

    def __init__(self, graceful=False):
        super().__init__(graceful)
        self._graceful = graceful
        self._serialized_default = self._DEF_SERIALIZED_DEFAULT
        self._deserialized_default = self._DEF_DESERIALIZED_DEFAULT

    @property
    def graceful(self):
        return self._graceful

    @graceful.setter
    def graceful(self, value):
        self._graceful = value

    def set_defaults(self, serialized, unserialized):
        self._serialized_default = serialized
        self._deserialized_default = unserialized

    def serialize(self, data: Transferrable) -> Serialized:
        try:
            serialized = json.dumps(data)
        except Exception:
            logger.error("Message serialization error", exc_info=True)
            if not self.graceful:
                raise SerializationError

            serialized = self._serialized_default

        return serialized

    def deserialize(self, msg: Serialized) -> Transferrable:
        body_txt = msg.decode("utf-8") if hasattr(msg, "decode") else msg
        try:
            deserialized = json.loads(body_txt)
        except json.JSONDecodeError:
            logger.error("Error deserializing message body", exc_info=True)
            if not self.graceful:
                raise SerializationError

            deserialized = self._deserialized_default

        return deserialized
