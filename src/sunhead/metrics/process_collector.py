
import os
import psutil

from typing import Callable


class ProcessCollector(object):
    """
    Collector for Standard Exports such as cpu and memory.
    """

    def __init__(self):
        self._pid = os.getpid()
        self._process = psutil.Process(self._pid)
        self._name_formatter = lambda x: x

    def set_name_formatter(self, func: Callable) -> None:
        self._name_formatter = func

    def get_snapshot(self):
        data = {
            "cpu_percent": self._process.cpu_percent(interval=None),
            "memory_percent": self._process.memory_percent()
        }
        return data

    def text_snapshot(self):
        s = self.get_snapshot()
        data = "".join(("{} {}\n".format(self._name_formatter(key), value) for key, value in s.items()))
        return data
