"""
Common bases for building CLI stuff
"""

from abc import ABCMeta, abstractmethod
import argparse
from typing import Dict


class Command(object, metaclass=ABCMeta):
    """

    """
    @abstractmethod
    def handler(self, options: Dict):
        """

        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def get_parser(self) -> argparse.ArgumentParser:
        """

        :return:
        """
        return argparse.ArgumentParser(description=self.handler.__doc__)

    @classmethod
    def get_subparser_name(cls) -> str:
        """

        :return:
        """
        return cls.__name__.lower()
