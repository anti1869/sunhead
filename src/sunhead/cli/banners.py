"""
Cozy utility to print ASCII banners and other stuff for your CLI app.
"""

import logging
import os


logger = logging.getLogger(__name__)


DEFAULT_BANNER_TEMPLATE = "\n\n{}\n"


def print_banner(filename: str, template: str = DEFAULT_BANNER_TEMPLATE) -> None:
    """
    Print text file to output.

    :param filename: Which file to print.
    :param template: Format string which specified banner arrangement.
    :return: Does not return anything
    """
    if not os.path.isfile(filename):
        logger.warning("Can't find logo banner at %s", filename)
        return

    with open(filename, "r") as f:
        banner = f.read()

    formatted_banner = template.format(banner)
    print(formatted_banner)
