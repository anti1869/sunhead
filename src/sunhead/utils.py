"""
Helper utilities that everyone needs.
"""

from collections import namedtuple
import importlib
import pkgutil
from typing import Sequence, Tuple, Any


ModuleDescription = namedtuple("ModuleDescription", "name path is_package")


def get_class_by_path(path: str) -> type:
    """Get class by conventional path. E.g. ``pkg.module.ClassName``"""
    module_path, class_name = path.rsplit('.', 1)
    mod = importlib.import_module(module_path)
    kls = getattr(mod, class_name)
    return kls


def get_submodule_list(package_path: str) -> Tuple[ModuleDescription]:
    """Get list of submodules for some package by its path. E.g ``pkg.subpackage``"""
    pkg = importlib.import_module(package_path)

    subs = (
        ModuleDescription(name=modname, path="{}.{}".format(package_path, modname), is_package=ispkg)
        for importer, modname, ispkg in pkgutil.iter_modules(pkg.__path__)
    )
    result = tuple(subs)
    return result
