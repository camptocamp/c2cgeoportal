# -*- coding: utf-8 -*-

# Copyright (c) 2016-2017, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


import contextlib
import logging
import os
import pyramid.events
from pyramid.httpexceptions import HTTPException
import re
import socket
import sqlalchemy.event
import time
import threading

BACKENDS = []
LOG = logging.getLogger(__name__)


@contextlib.contextmanager
def timer_context(key):
    """
    Add a duration measurement to the stats using the duration the context took to run
    :param key: The path of the key, given as a list.
    """
    measure = timer(key)
    yield
    measure.stop()


def timer(key=None):
    """
    Create a timer for the given key. The key can be omitted, but then need to be specified
    when stop is called.
    :param key: The path of the key, given as a list.
    :return: An instance of _Timer
    """
    assert key is None or isinstance(key, list)
    return _Timer(key)


class _Timer:
    """
    Allow to measure the duration of some activity
    """
    def __init__(self, key):
        self._key = key
        self._start = time.time()

    def stop(self, key_final=None):
        if key_final is not None:
            self._key = key_final
        for backend in BACKENDS:
            backend.timer(self._key, time.time() - self._start)


class _MemoryBackend:
    def __init__(self):
        self._timers = {}  # key => (nb, sum, min, max)
        self._stats_lock = threading.Lock()
        LOG.info("Starting a MemoryBackend for stats")

    def timer(self, key, duration):
        """
        Add a duration measurement to the stats.
        """
        the_key = "/".join(key)
        with self._stats_lock:
            cur = self._timers.get(the_key)
            if cur is None:
                self._timers[the_key] = (1, duration, duration, duration)
            else:
                self._timers[the_key] = (cur[0] + 1, cur[1] + duration, min(cur[2], duration),
                                         max(cur[3], duration))

    def get_stats(self, request):
        reset = request.params.get("reset", "0") == "1"
        timers = {}
        with self._stats_lock:
            for key, value in self._timers.iteritems():
                timers[key] = {
                    "nb": value[0],
                    "avg_ms": int(round((value[1] / value[0]) * 1000.0)),
                    "min_ms": int(round(value[2] * 1000.0)),
                    "max_ms": int(round(value[3] * 1000.0)),
                }
            if reset:
                self._timers.clear()
        return {"timers": timers}


INVALID_KEY_CHARS = re.compile(r"[:|\.]")


class _StatsDBackend:  # pragma: no cover
    def __init__(self, address, prefix):
        self._prefix = prefix
        if self._prefix != "" and not self._prefix.endswith("."):
            self._prefix += "."

        host, port = address.rsplit(":")
        host = host.strip("[]")
        addrinfo = socket.getaddrinfo(host, port, 0, 0, socket.IPPROTO_UDP)
        af, socktype, proto, _, sa = addrinfo[0]
        LOG.info("Starting a StatsDBackend for %s stats: %s -> %s", prefix, address, repr(sa))

        self._socket = socket.socket(af, socktype, proto)
        self._socket.setblocking(0)
        self._socket.connect(sa)

    def _key(self, key):
        return self._prefix + ".".join([INVALID_KEY_CHARS.sub("_", i) for i in key])

    def timer(self, key, duration):
        the_key = self._key(key)
        message = "{0!s}:{1!s}|ms".format(the_key, int(round(duration * 1000.0)))
        try:
            self._socket.send(message)
        except:
            pass  # Ignore errors (must survive if stats cannot be sent)


def _create_finished_cb(kind, measure):  # pragma: no cover
    def finished_cb(request):
        if request.exception is not None:
            if isinstance(request.exception, HTTPException):
                status = request.exception.code
            else:
                status = 500
        else:
            status = request.response.status_code
        if request.matched_route is None:
            name = "_not_found"
        else:
            name = request.matched_route.name
        key = [kind, request.method, name, str(status)]
        measure.stop(key)
    return finished_cb


def _request_callback(event):  # pragma: no cover
    """
    Callback called when a new HTTP request is incoming.
    """
    measure = timer()
    event.request.add_finished_callback(_create_finished_cb("route", measure))


def _before_rendered_callback(event):  # pragma: no cover
    """
    Callback called when the rendering is starting.
    """
    request = event.get("request")
    if request:
        measure = timer()
        request.add_finished_callback(_create_finished_cb("render", measure))


def _simplify_sql(sql):
    """
    Simplify SQL statements to make them easier on the eye and shorter for the stats.
    """
    sql = " ".join(sql.split("\n"))
    sql = re.sub(r"  +", " ", sql)
    sql = re.sub(r"SELECT .*? FROM", "SELECT FROM", sql)
    sql = re.sub(r"INSERT INTO (.*?) \(.*", r"INSERT INTO \1", sql)
    sql = re.sub(r"SET .*? WHERE", "SET WHERE", sql)
    sql = re.sub(r"IN \((?:%\(\w+\)\w(?:, *)?)+\)", "IN (?)", sql)
    return re.sub(r"%\(\w+\)\w", "?", sql)


def _before_cursor_execute(conn, cursor, statement,
                           parameters, context, executemany):  # pragma: no cover
    measure = timer(["sql", _simplify_sql(statement)])

    def after(*args, **kwargs):
        measure.stop()

    sqlalchemy.event.listen(conn, "after_cursor_execute", after, once=True)


def _before_commit(session):  # pragma: no cover
    measure = timer(["sql", "commit"])

    def after(*args, **kwargs):
        measure.stop()

    sqlalchemy.event.listen(session, "after_commit", after, once=True)


def init_db_spy():  # pragma: no cover
    """
    Subscribe to SQLAlchemy events in order to get some stats on DB interactions.
    """
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session
    sqlalchemy.event.listen(Engine, "before_cursor_execute", _before_cursor_execute)
    sqlalchemy.event.listen(Session, "before_commit", _before_commit)


def init_pyramid_spy(config):  # pragma: no cover
    """
    Subscribe to Pyramid events in order to get some stats on route time execution.
    :param config: The Pyramid config
    """
    config.add_subscriber(_request_callback, pyramid.events.NewRequest)
    config.add_subscriber(_before_rendered_callback, pyramid.events.BeforeRender)


def _get_env_or_settings(config, what_env, what_vars, default):
    from_env = os.environ.get(what_env)
    if from_env is not None:  # pragma: no cover
        return from_env
    stats = config.get_settings().get("stats", {})
    return stats.get(what_vars, default)


def init_backends(config):
    """
    Initialize the backends according to the configuration.
    :param config: The Pyramid config
    """
    if _get_env_or_settings(config, "STATS_VIEW", "view", False):  # pragma: no cover
        memory_backend = _MemoryBackend()
        BACKENDS.append(memory_backend)

        config.add_route("read_stats_json", r"/stats.json", request_method="GET")
        config.add_view(memory_backend.get_stats, route_name="read_stats_json", renderer="json")

        config.add_route("read_stats_html", r"/stats.html", request_method="GET")
        config.add_view(memory_backend.get_stats, route_name="read_stats_html",
                        renderer="c2cgeoportal:templates/stats.html")

    statsd_address = _get_env_or_settings(config, "STATSD_ADDRESS", "statsd_address", None)
    if statsd_address is not None:  # pragma: no cover
        statsd_prefix = _get_env_or_settings(config, "STATSD_PREFIX", "statsd_prefix", "")
        BACKENDS.append(_StatsDBackend(statsd_address, statsd_prefix))


def init(config):
    """
    Initialize the whole stats module.
    :param config: The Pyramid config
    """
    init_backends(config)
    if BACKENDS:  # pragma: no cover
        init_pyramid_spy(config)
        init_db_spy()
