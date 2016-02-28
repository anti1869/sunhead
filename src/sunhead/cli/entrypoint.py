"""
Entry point of SunHead commands.
"""

from typing import Optional, Iterable

from sunhead.conf import settings
from sunhead.cli.abc import Command
from sunhead.cli.commands.runserver import Runserver
from sunhead.cli.helpers import parse_args, run_command


default_commands = (
    Runserver(),
)

default_fallback = "sunhead.global_settings"


def main(
    commands: Optional[Iterable[Command]] = None,
    settings_ennvar: Optional[str] = None,
    fallback_settings_module: Optional[str] = None
) -> None:

    commands = commands or default_commands
    fallback_settings = fallback_settings_module or default_fallback

    args = parse_args(commands)
    settings.configure(args['settings'], settings_ennvar, fallback_settings)
    run_command(args, commands)
