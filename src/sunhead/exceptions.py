"""
Collection of custom exceptions
"""


class SunHeadException(Exception):
    """Common base for other exceptions"""


class ImproperlyConfigured(SunHeadException):
    """There is an error in configuration file"""
