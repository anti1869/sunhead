"""
Collecting and exposing runtime metrics. Mostly built around ``Prometheus``, but may
add support for other things later.

Usage::

    class Smth(object):

        def __init__(self):
            self.metrics = get_metrics("reporter")
            self.metrics.add_summary("reporter_data_generation_speed", "Report generation speed items/sec")

        def job(self):
            # smth
            self.metrics.summaries["reporter_data_generation_speed"].observe(34.44)

Then, if such feature is enabled, metrics could be reach at ``http://server/metrics`` endpoint.
"""

from itertools import chain
import logging
from typing import Dict, Iterable

from prometheus_client import (
    Gauge, Counter, Summary, Histogram, generate_latest, core, exposition, PROCESS_COLLECTOR,
)  # noqa

from sunhead.conf import settings
from sunhead.exceptions import (
    DuplicateMetricException, IncorrectMetricsSnapshotFormatException,
)
from sunhead.metrics.process_collector import ProcessCollector


logger = logging.getLogger(__name__)
__all__ = ("Metrics", "get_metrics", "get_all_metrics", )


class Metrics(object):

    # Not sure it's needed
    DEFAULT_APP_PREFIX = "sunhead"
    SNAPSHOT_PROMETHEUS = "prometheus"

    def __init__(self):
        self._app_prefix = self.DEFAULT_APP_PREFIX

        self._data = {
            "counters": {},
            "gauges": {},
            "summaries": {},
            "histograms": {},
        }

        self._process_collector = None

        if not getattr(settings, "DISABLE_PROCESS_METRICS", False) \
                and not getattr(settings, "USE_PROMETHEUS_PROCESS_METRICS", False):
            self._process_collector = ProcessCollector()
            self._process_collector.set_name_formatter(self.prefix)
            self._disable_prometheus_process_collector()

    def _disable_prometheus_process_collector(self) -> None:
        """
        There is a bug in SDC' Docker implementation and intolerable prometheus_client code, due to which
        its process_collector will fail.

        See https://github.com/prometheus/client_python/issues/80
        """
        logger.info("Removing prometheus process collector")
        try:
            core.REGISTRY.unregister(PROCESS_COLLECTOR)
        except KeyError:
            logger.debug("PROCESS_COLLECTOR already removed from prometheus")

    @property
    def counters(self) -> Dict:
        return self._data["counters"]

    @property
    def gauges(self) -> Dict:
        return self._data["gauges"]

    @property
    def summaries(self) -> Dict:
        return self._data["summaries"]

    @property
    def histograms(self) -> Dict:
        return self._data["histograms"]

    @property
    def all_metrics(self) -> Iterable:
        all_metrics = chain(
            self.counters.values(), self.gauges.values(), self.summaries.values(), self.histograms.values()
        )
        return all_metrics

    def add_counter(self, name: str, *args) -> None:
        if name in self.counters:
            raise DuplicateMetricException("Counter %s already exist" % name)
        self.counters[name] = (Counter(name, *args))

    def add_gauge(self, name: str, *args) -> None:
        if name in self.gauges:
            raise DuplicateMetricException("Gauge %s already exist" % name)
        self.gauges[name] = (Gauge(name, *args))

    def add_summary(self, name: str, *args) -> None:
        if name in self.summaries:
            raise DuplicateMetricException("Summary %s already exist" % name)
        self.summaries[name] = (Summary(name, *args))

    def add_histogram(self, name: str, *args, **kwargs) -> None:
        if name in self.histograms:
            raise DuplicateMetricException("Histogram %s already exist" % name)
        self.histograms[name] = (Histogram(name, *args, **kwargs))

    def text_snapshot(self, output_format: str = SNAPSHOT_PROMETHEUS) -> str:
        fn_name = "_get_{}_snapshot".format(output_format)
        if not hasattr(self, fn_name):
            raise IncorrectMetricsSnapshotFormatException("No such snapshot format: %s" % output_format)
        result = getattr(self, fn_name)()
        return result

    def _get_prometheus_snapshot(self) -> str:
        # Actually, this will produce all registered metrics, from all Metrics instances,
        # due to the ``core.REGISTRY`` nature.
        # Will fix it sometimes later.
        snapshot = generate_latest(core.REGISTRY).decode()
        if self._process_collector is not None:
            snapshot += self._process_collector.text_snapshot()
        return snapshot

    @property
    def app_name_prefix(self) -> str:
        return self._app_prefix

    @app_name_prefix.setter
    def app_name_prefix(self, value: str) -> None:
        self._app_prefix = value

    def prefix(self, name: str):
        """
        Prefix metrics name with configured app prefix. Use as shortcut.

        :param name: Metric name (or any string, really).
        """
        return "{}_{}".format(self.app_name_prefix, name)


_metrics = {}
_NAME_GLOBAL = "global"


def get_metrics(name: str = _NAME_GLOBAL) -> Metrics:
    metrics = _metrics.setdefault(name, Metrics())
    return metrics


def get_all_metrics():
    return _metrics.values()
