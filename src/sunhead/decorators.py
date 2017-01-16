"""
Miscellaneous decorators to make your life easier.
"""

import logging


default_logger = logging.getLogger(__name__)


DEPRECATION_MESSAGE = "WARNING: Using {name} is deprecated. It will be removed soon"


class Sentinel(object):
    """Use this instead of None"""


def cached_property():
    """
    Handy utility to build caching properties in your classes.
    Decorated code will be run only once and then result will be stored in private class property
    with the given name. When called for the second time, property will return cached value.


    :param storage_var_name: Name of the class property to store cached data.
    :type storage_var_name: str
    :return: Decorator for the class property
    """
    def _stored_value(f):
        storage_var_name = "__{}".format(f.__name__)

        def _wrapper(self, *args, **kwargs):
            value_in_cache = getattr(self, storage_var_name, Sentinel)
            if value_in_cache is not Sentinel:
                return value_in_cache
            calculated_value = f(self, *args, **kwargs)
            setattr(self, storage_var_name, calculated_value)
            return calculated_value
        return _wrapper
    return _stored_value


def deprecated(message=DEPRECATION_MESSAGE, logger=None):
    """
    This decorator will simply print warning before running decoratee.
    So, presumably, you want to use it with console-based commands.

    :return: Decorator for the function.
    """
    if logger is None:
        logger = default_logger
    def _deprecated(f):
        def _wrapper(*args, **kwargs):
            f_name = f.__name__
            logger.warning(message.format(name=f_name))
            result = f(*args, **kwargs)
            return result
        return _wrapper
    return _deprecated
