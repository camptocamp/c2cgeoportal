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
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "10"))

timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))

max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", "100"))
worker_tmp_dir = "/dev/shm"  # noqa: S108
limit_request_line = int(os.environ.get("GUNICORN_LIMIT_REQUEST_LINE", "8190"))

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
        },
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
