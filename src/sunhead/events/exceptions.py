"""
Exceptions, related to messaging.
"""


class StreamConnectionError(Exception):
    """Error connecting transport"""


class ConsumerError(StreamConnectionError):
    """Some error in message consumer"""


class PublisherError(StreamConnectionError):
    """Problem with message publisher"""


class SerializationError(Exception):
    """Error serializing or deserializing data"""
