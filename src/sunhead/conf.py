"""
Settings and configuration for every application in a package.

Some code taken from Django settings
https://github.com/django/django/blob/master/django/conf/__init__.py
"""

import importlib
import os
from typing import Iterator
from logging.config import dictConfig
from importlib import import_module

import yaml

from sunhead.exceptions import ImproperlyConfigured


DEFAULT_ENVIRONMENT_VARIABLE = "SUNHEAD_SETTINGS_MODULE"
GLOBAL_CONFIG_MODULE = "sunhead.global_settings"


_common_places = [
    os.path.expanduser("~"),
    "/etc/",
]


class Settings(object):

    def __init__(self):
        self._configured = False
        self._configuring = False
        self._envvar = DEFAULT_ENVIRONMENT_VARIABLE

    def __getattribute__(self, item):
        # Some sort of Lazy Settings implementation.
        # All this stuff is to allow using custom settings envvar names.
        # Settings will be configured upon first element fetch or manually, using ``configure`` method

        passthrough = {"_configuring", "_configured", "configure"}

        if item not in passthrough and not self._configuring and not self._configured:
            self.configure()

        return super().__getattribute__(item)

    def configure(self, settings_module: str = None, custom_envvar: str = None, fallback_module: str = None) -> None:

        # Disable __getattribute__ hook while this method is run.
        self._configuring = True

        if custom_envvar:
            self._envvar = custom_envvar

        global_config = import_module(GLOBAL_CONFIG_MODULE)
        settings_module_name = settings_module or self.get_settings_module_name(fallback_module)

        # update this dict from global settings (but only for ALL_CAPS settings)
        for setting in dir(global_config):
            if setting.isupper():
                setattr(self, setting, getattr(global_config, setting))

        # store the settings module in case someone later cares
        self.SETTINGS_MODULE = settings_module_name

        mod = import_module(self.SETTINGS_MODULE)

        tuple_settings = (
            # Add your tuple settings here
            # "INSTALLED_APPS"
        )
        self._explicit_settings = set()
        for setting in dir(mod):
            if setting.isupper():
                setting_value = getattr(mod, setting)

                if (setting in tuple_settings and
                        not isinstance(setting_value, (list, tuple))):
                    raise ImproperlyConfigured(
                        "The %s setting must be a list or a tuple. Please fix your settings." % setting)
                setattr(self, setting, setting_value)
                self._explicit_settings.add(setting)

        self.update_from_config_file()
        self.configure_logging()

        # Disable __gettattr__ hook completely
        self._configured = True
        self._configuring = False

    def get_settings_module_name(self, fallback_module):
        name = os.environ.get(self._envvar, None) or fallback_module
        if not name:
            raise ImproperlyConfigured(
                "Settings module not found. Got %s in %s var and there is no fallback provided." % (name, self._envvar)
            )
        return name

    def is_overridden(self, setting):
        return setting in self._explicit_settings

    def __repr__(self):
        return '<%(cls)s "%(settings_module)s">' % {
            'cls': self.__class__.__name__,
            'settings_module': self.SETTINGS_MODULE,
        }

    def update_from_config_file(self):
        filename = getattr(self, "CONFIG_FILENAME", None)
        if not filename:
            return

        config_path = self.discover_config_path(filename)
        for setting, setting_value in self.gen_from_yaml_config(config_path):
            # if setting == "LOGGING":  # Special case, will think better solution later
            #     setting_value = self.get_overriden_dict_config(setting_value)
            setattr(self, setting, setting_value)

    def discover_config_path(self, config_filename: str) -> str:
        """
        Search for config file in a number of places.
        If there is no config file found, will return None.

        :param config_filename: Config file name or custom path to filename with config.
        :return: Path to the discovered config file or None.
        """

        if config_filename and os.path.isfile(config_filename):
            return config_filename

        for place in _common_places:
            config_path = os.path.join(place, config_filename)
            if os.path.isfile(config_path):
                return config_path

        return

    def gen_from_yaml_config(self, config_path: str) -> Iterator:
        """
        Convention is to uppercase first level keys.

        :param config_path: Valid path to the yml config file.
        :return: Config loaded from yml file
        """
        if not config_path:
            return {}

        with open(config_path, 'r') as f:
            yaml_config = yaml.load(f)

        gen = map(lambda x: (x[0].upper(), x[1]), yaml_config.items())

        return gen

    def configure_logging(self):
        logging = getattr(self, "LOGGING", None)
        if not logging:
            return

        self.remove_unused_handlers(logging, {})
        dictConfig(logging)

    def remove_unused_handlers(self, dict_config, requested_handlers):
        should_not_be_empty = (
            ("file", "filename"),
            ("sentry", "dsn"),
            ("syslog", "address"),
        )
        for handler, key in should_not_be_empty:
            self.remove_handler_if_not_configured(dict_config, {}, handler, key)

    def remove_handler_if_not_configured(self, dict_config, requested_handlers, handler_name, check_key) -> None:
        """
        Remove ``handler_name`` from ``dict_config`` and ``requested_handlers`` if ``check_key`` is empty.
        """
        try:
            if not dict_config["handlers"][handler_name][check_key]:
                dict_config["handlers"].pop(handler_name)
                if handler_name in requested_handlers:
                    requested_handlers.remove(handler_name)
        except KeyError:
            # Ignore key errors
            pass


settings = Settings()

