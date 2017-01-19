"""
JSON message body serializer
"""

import logging
from datetime import datetime, timedelta
import enum
import uuid

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

    @classmethod
    def json_serial(cls, obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, datetime):
            serial = obj.isoformat()

        elif issubclass(obj.__class__, enum.Enum):
            serial = obj.value

        elif isinstance(obj, timedelta):
            serial = str(obj)

        elif isinstance(obj, set):
            serial = list(x for x in obj)

        elif isinstance(obj, uuid.UUID):
            serial = str(obj)

        # FIXME: if you want to add one more custom serializer, think twice about `singledispatch`

        else:
            raise TypeError("Type not serializable %s in %s" % (type(obj), obj))

        return serial

    @property
    def graceful(self):
        return self._graceful

    @graceful.setter
    def graceful(self, value):
        self._graceful = value

    def set_defaults(self, serialized, unserialized):
        self._serialized_default = serialized
        self._deserialized_default = unserialized

    def serialize(self, data: Transferrable, **kwargs) -> Serialized:
        kwargs.setdefault("default", self.json_serial)
        try:
            serialized = json.dumps(data, **kwargs)
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
