"""
Collection of custom exceptions
"""


class SunHeadException(Exception):
    """Common base for other exceptions"""


class ImproperlyConfigured(SunHeadException):
    """There is an error in configuration file"""


class MetricsException(SunHeadException):
    """Error in metrics module"""


class DuplicateMetricException(MetricsException):
    """Duplicate metric"""


class IncorrectMetricsSnapshotFormatException(MetricsException):
    """No such format"""