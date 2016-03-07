"""

"""


import argparse

import importlib

from sunhead.cli.abc import Command


class Runserver(Command):
    """
    Start HTTP Server
    """

    DEFAULT_SERVER_CLASS = 'sunhead.workers.http.server.Server'

    def __init__(self, server_class_name=None):
        self.server_class_name = server_class_name or self.DEFAULT_SERVER_CLASS

    def get_server_class(self):
        # fixme: add errors handling
        module, name = self.server_class_name.rsplit('.', 1)
        mod = importlib.import_module(module)
        server_class = getattr(mod, name)
        return server_class

    def handler(self, options) -> None:
        srv_class = self.get_server_class()
        srv = srv_class(fd=options['fd'], host=options['host'], port=options['port'])
        srv.run()

    def get_parser(self):
        parser_command = argparse.ArgumentParser(description="Run application server")
        parser_command.add_argument(
            "--fd",
            dest="fd",
            type=int,
            help="FD is filled by Circus manager",
        )
        parser_command.add_argument(
            "host",
            help="IP address for listen",
            nargs="?",
        )
        parser_command.add_argument(
            "-p", "--port",
            help="TCP port address for listen",
        )
        return parser_command
