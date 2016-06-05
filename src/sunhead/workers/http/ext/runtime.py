"""
Runtime stats extension for the HTTPServerWorker implementation classes.

Usage: Just put in as mixin in your concrete implementations::

..code-block:: python

    from brandt.workers.http.server import Server
    from brandt.workers.http.ext.runtime import ServerStatsMixin

    class MyServer(ServerStatsMixin, Server):
        pass

And you're magically good already.

If there is ServerStreamConnection enabled on server, this extension will even send
runtime stats to the Stream!

There are two endpoints exposed:

- /runtime/ - Some status info
- /metrics - Metrics snapshot in Prometheus-compliant format

Enjoy.
"""

import logging
from asyncio import ensure_future

from aiohttp.web import Application

from sunhead.conf import settings
from sunhead.metrics import get_metrics, Metrics
from sunhead.periodical import crontab
from sunhead.rest.views import JSONView, BasicView
from sunhead.version import get_version
from sunhead.workers.http.server import BaseServerMixin


logger = logging.getLogger(__name__)


async def runtime_stats_middleware(app, handler):
    async def middleware_handler(request):
        app.setdefault("_request_cnt", 0)
        app["_request_cnt"] += 1
        if hasattr(app, "metrics"):
            metrics_app_name = getattr(app, "metrics_app_name", "sunhead_httpserver")
            app.metrics.counters["{}_requests_total".format(metrics_app_name)].inc()
        return await handler(request)
    return middleware_handler


class RuntimeStatsView(JSONView):

    async def get(self):
        """Printing runtime statistics in JSON"""

        context_data = self.get_context_data()
        context_data.update(getattr(self.request.app, "stats", {}))

        response = self.json_response(context_data)
        return response

    def get_context_data(self):
        # TODO: Add more useful stuff here
        context_data = {
            "pkg_version": getattr(settings, "PKG_VERSION", None),
        }
        return context_data


class PrometheusMetricsView(BasicView):

    async def get(self):
        snapshot = self.request.app.metrics.text_snapshot(Metrics.SNAPSHOT_PROMETHEUS)
        return self.basic_response(text=snapshot)


class ServerStatsMixin(BaseServerMixin):

    RPS_POLLING_SECS = 5
    MESSAGE_PRODUCING_SECS = 5

    DISPLAYED_SERVER_PROPERTIES = ("guid", "host", "port", "app_name")

    @property
    def _app_container(self) -> Application:
        return getattr(self, "app")

    @property
    def _metrics_app_name(self) -> str:
        return getattr(self, "app_name").replace(".", "_")

    def init_requirements(self, *args, **kwargs):
        getattr(super(), "init_requirements")(*args, **kwargs)
        self.init_runtime_stats()
        self.init_metrics()

    def get_middlewares(self, *args, **kwargs):
        mw = getattr(super(), "get_middlewares")(*args, **kwargs)
        mw += [runtime_stats_middleware]
        return mw

    def get_urlpatterns(self):
        ep = getattr(settings, "RUNTIME_STATS_ENDPOINT", "/runtime/")
        prometheus_ep = getattr(settings, "PROMETHEUS_METRICS_ENDPOINT", "/metrics")
        patterns = getattr(super(), "get_urlpatterns")()
        patterns += (
            ("GET", ep, RuntimeStatsView),
            ("GET", prometheus_ep, PrometheusMetricsView),
        )
        return patterns

    def get_class_props(self):
        props = {
            name.lower(): getattr(self, name)
            for name in self.DISPLAYED_SERVER_PROPERTIES if hasattr(self, name)
        }
        return props

    def init_runtime_stats(self):
        stats = {
            "sunhead_version": get_version(full=True),
            "rps": 0,
        }
        stats.update(self.get_class_props())

        self._app_container.stats = stats
        self._rps_calc = crontab(
            "* * * * * */{}".format(self.RPS_POLLING_SECS), func=self.recalc_rps, start=True)
        self._produce_stats_msg = crontab(
            "* * * * * */{}".format(self.MESSAGE_PRODUCING_SECS), func=self.send_runtime_stats, start=True)

    def init_metrics(self):
        metrics = get_metrics("http_server")
        metrics.app_name_prefix = self._metrics_app_name
        metrics.add_counter(metrics.prefix("requests_total"), "Total requests")
        self._app_container.metrics = metrics
        self._app_container.metrics_app_name = self._metrics_app_name

    async def recalc_rps(self):
        reqs = self._app_container.get("_request_cnt", 0)
        rps = float(reqs) / self.RPS_POLLING_SECS
        self._app_container["_request_cnt"] = 0
        stats_container = self._get_stats_container()
        if stats_container is not None:
            stats_container["rps"] = rps

    def _get_stats_container(self):
        stats_container = getattr(self._app_container, "stats", None)
        return stats_container

    async def send_runtime_stats(self) -> None:
        # TODO: Use interfaces here
        stream = getattr(self._app_container, "stream", None)
        if not settings.STATS_PRODUCER_ENABLED or stream is None or not hasattr(stream, "publish"):
            logger.info("Producer disabled or can't find stream interface, disabling runtime message producer")
            self._produce_stats_msg.stop()
            return

        stats_container = self._get_stats_container()

        try:
            ensure_future(
                stream.publish(stats_container, topics=(settings.STATS_PRODUCER_ROUTING_KEY,))
            )
            logger.debug("Runtime stats sent to the stream")
        except Exception:
            logger.warning("Can't send stats to the stream", exc_info=True)
