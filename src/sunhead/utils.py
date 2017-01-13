"""
Helper utilities that everyone needs.
"""

import asyncio
from collections import namedtuple, OrderedDict
from datetime import datetime
from enum import Enum
import importlib
import logging
import pkgutil
import re
from typing import Sequence, Tuple, Dict, Optional, Any

from dateutil import tz

from sunhead.conf import settings


logger = logging.getLogger(__name__)


ModuleDescription = namedtuple("ModuleDescription", "name path is_package")


def get_class_by_path(class_path: str, is_module: Optional[bool] = False) -> type:
    """
    Get class by its name within a package structure.

    :param class_path: E.g. brandt.some.module.ClassName
    :param is_module: Whether last item is module rather than class name
    :return: Class ready to be instantiated.
    """

    if is_module:
        try:
            backend_module = importlib.import_module(class_path)
        except ImportError:
            logger.warning("Can't import backend with name `%s`", class_path)
            raise
        else:
            return backend_module

    module_name, class_name = class_path.rsplit('.', 1)

    try:
        backend_module = importlib.import_module(module_name)
    except ImportError:
        logger.error("Can't import backend with name `%s`", module_name)
        raise

    try:
        backend_class = getattr(backend_module, class_name)
    except AttributeError:
        logger.error("Can't get backend class `%s` from `%s`", class_name, module_name)
        raise

    return backend_class


def get_submodule_list(package_path: str) -> Tuple[ModuleDescription, ...]:
    """Get list of submodules for some package by its path. E.g ``pkg.subpackage``"""
    pkg = importlib.import_module(package_path)

    subs = (
        ModuleDescription(
            name=modname,
            path="{}.{}".format(package_path, modname), is_package=ispkg
        )
        for importer, modname, ispkg in pkgutil.iter_modules(pkg.__path__)
    )
    result = tuple(subs)
    return result


def camel_to_underscore(kls: type) -> str:
    parts = re.findall('[A-Z][^A-Z]*', kls.__name__)
    name = '_'.join(part.lower() for part in parts)
    return name


# LibraryObjectDefinition = namedtuple('NamedObjectDefinition', 'name kls')


# TODO: Activate when will implement recursive submodule list
# def get_classes_from_libraries(object_libraries, base_class) -> Set[LibraryObjectDefinition]:
#     definitions = set()
#     for path in object_libraries:
#         modules = get_submodule_list(path, recursive=True)
#         for module in map(lambda x: get_backend_class(x.path, is_module=True), modules):
#             block_classes = get_subclasses_from_module(module, base_class)
#             for kls in block_classes:
#                 definitions.add(
#                     LibraryObjectDefinition(camel_to_underscore(kls), kls)
#                 )
#     return definitions


async def parallel_results(future_map: Sequence[Tuple]) -> Dict:
    """
    Run parallel execution of futures and return mapping of their results to the provided keys.
    Just a neat shortcut around ``asyncio.gather()``

    :param future_map: Keys to futures mapping, e.g.: ( ('nav', get_nav()), ('content, get_content()) )
    :return: Dict with futures results mapped to keys {'nav': {1:2}, 'content': 'xyz'}
    """
    ctx_methods = OrderedDict(future_map)
    fs = list(ctx_methods.values())
    results = await asyncio.gather(*fs)
    results = {
        key: results[idx] for idx, key in enumerate(ctx_methods.keys())
    }
    return results


def positive_int(integer_string: str, strict: bool = False, cutoff: Optional[int] = None) -> int:
    """
    Cast a string to a strictly positive integer.
    """
    ret = int(integer_string)
    if ret < 0 or (ret == 0 and strict):
        raise ValueError()
    if cutoff:
        ret = min(ret, cutoff)
    return ret


def get_configured_tz_now() -> datetime:
    tzname = getattr(settings, 'TZ', 'Europe/Moscow')
    tzinfo = tz.gettz(tzname)
    now = datetime.now(tzinfo)
    return now


def choices_from_enum(source: Enum) -> Tuple[Tuple[Any, str], ...]:
    """
    Makes tuple to use in Django's Fields ``choices`` attribute.
    Enum members names will be titles for the choices.

    :param source: Enum to process.
    :return: Tuple to put into ``choices``
    """
    result = tuple((s.value, s.name.title()) for s in source)
    return result
