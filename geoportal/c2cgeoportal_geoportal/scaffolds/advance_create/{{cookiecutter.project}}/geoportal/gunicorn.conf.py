# Copyright (c) 2019-2024, Camptocamp SA
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

###
# app configuration
# https://docs.gunicorn.org/en/stable/settings.html
###

import os

import gunicorn.arbiter
import gunicorn.workers.base
from c2cwsgiutils import get_config_defaults, prometheus
from prometheus_client import multiprocess

bind = ":8080"

worker_class = "gthread"
workers = int(os.environ.get("GUNICORN_WORKERS", 2))
threads = int(os.environ.get("GUNICORN_THREADS", 10))

timeout = int(os.environ.get("GUNICORN_TIMEOUT", 120))

max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", 100))
worker_tmp_dir = "/dev/shm"  # nosec
limit_request_line = int(os.environ.get("GUNICORN_LIMIT_REQUEST_LINE", 8190))

accesslog = "-"
access_log_format = os.environ.get(
    "GUNICORN_ACCESS_LOG_FORMAT",
    '%(H)s %({Host}i)s %(m)s %(U)s?%(q)s "%(f)s" "%(a)s" %(s)s %(B)s %(D)s %(p)s',
)

###
# logging configuration
# https://docs.python.org/3/library/logging.config.html#logging-config-dictschema
###
logconfig_dict = {
    "version": 1,
    "root": {
        "level": os.environ["OTHER_LOG_LEVEL"],
        "handlers": [os.environ["LOG_TYPE"]],
    },
    "loggers": {
        "gunicorn.error": {"level": os.environ["GUNICORN_LOG_LEVEL"]},
        # "level = INFO" logs SQL queries.
        # "level = DEBUG" logs SQL queries and results.
        # "level = WARN" logs neither.  (Recommended for production systems.)
        "sqlalchemy.engine": {"level": os.environ["SQL_LOG_LEVEL"]},
        "dogpile.cache": {"level": os.environ["DOGPILECACHE_LOG_LEVEL"]},
        "c2cwsgiutils": {"level": os.environ["C2CWSGIUTILS_LOG_LEVEL"]},
        "c2cgeoportal_commons": {"level": os.environ["C2CGEOPORTAL_LOG_LEVEL"]},
        "c2cgeoportal_geoportal": {"level": os.environ["C2CGEOPORTAL_LOG_LEVEL"]},
        "c2cgeoportal_admin": {"level": os.environ["C2CGEOPORTAL_LOG_LEVEL"]},
        "{{cookiecutter.package}}_geoportal": {"level": os.environ["LOG_LEVEL"]},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": "ext://sys.stdout",
        },
        "json": {
            "class": "c2cwsgiutils.pyramid_logging.JsonLogHandler",
            "formatter": "generic",
            "stream": "ext://sys.stdout",
        },
    },
    "formatters": {
        "generic": {
            "format": "%(asctime)s [%(process)d] [%(levelname)-5.5s] %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        }
    },
}

raw_paste_global_conf = ["=".join(e) for e in get_config_defaults().items()]


def on_starting(server: gunicorn.arbiter.Arbiter) -> None:
    """
    Will start the prometheus server.

    Called just before the master process is initialized.
    """

    del server

    prometheus.start()


def post_fork(server: gunicorn.arbiter.Arbiter, worker: gunicorn.workers.base.Worker) -> None:
    """
    Will cleanup the configuration we get from the main process.

    Called just after a worker has been forked.
    """

    del server, worker

    prometheus.cleanup()


def child_exit(server: gunicorn.arbiter.Arbiter, worker: gunicorn.workers.base.Worker) -> None:
    """
    Remove the metrics for the exited worker.

    Called just after a worker has been exited, in the master process.
    """

    del server

    multiprocess.mark_process_dead(worker.pid)
