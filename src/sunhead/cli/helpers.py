"""

"""
import argparse
from typing import Optional, Dict, Iterable

from sunhead.cli.abc import Command


def parse_args(commands: Iterable[Command], args: Optional[Iterable[str]] = None) -> Dict:
    parser = argparse.ArgumentParser(description="SunHead management tool.")
    parser.add_argument(
        "--settings",
        dest="settings",
        type=str,
        required=False,
        help="Custom settings module",
    )

    # Add commands
    subparsers = parser.add_subparsers(title="Available commands", metavar="COMMAND")
    for command in commands:
        command_parser = command.get_parser()
        sp = subparsers.add_parser(
            command.get_subparser_name(),
            parents=[command_parser],
            help=command_parser.description,
            description=command_parser.description,
            add_help=False,
        )
        sp.set_defaults(func=command.handler)

    parsed_args = vars(parser.parse_args(args))
    return parsed_args


def run_command(args: Dict, commands: Iterable[Command]):
    # Is there command defined?
    func = args.pop("func", None)
    if func is None:
        parse_args(commands, ["--help"])
        return
    func(args)
