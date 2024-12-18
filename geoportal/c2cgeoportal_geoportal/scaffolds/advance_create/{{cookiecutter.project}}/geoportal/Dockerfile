ARG {{cookiecutter.geomapfish_version_tag}}
ARG {{cookiecutter.geomapfish_major_version_tag}}

FROM camptocamp/geomapfish-tools:{{cookiecutter.geomapfish_version_tag_env}} AS builder
LABEL maintainer Camptocamp "info@camptocamp.com"

COPY requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache \
    python3 -m pip install --disable-pip-version-check --requirement=/tmp/requirements.txt

WORKDIR /app
COPY webpack.*.js Makefile CONST_Makefile /app/
COPY {{cookiecutter.package}}_geoportal/static-ngeo /app/{{cookiecutter.package}}_geoportal/static-ngeo
RUN make apps

COPY . /app

RUN make build
RUN mv webpack.apps.js webpack.apps.js.tmpl

ENTRYPOINT [ "/usr/bin/eval-templates" ]
CMD [ "webpack", "serve", "--open", "--mode=development", "--watch", "--no-inline" ]

###############################################################################

FROM camptocamp/geomapfish:{{cookiecutter.geomapfish_major_version_tag_env}} AS runner

COPY requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache \
    python3 -m pip install --disable-pip-version-check --requirement=/tmp/requirements.txt

WORKDIR /app
COPY . /app
# Workaround, see:https://github.com/moby/moby/issues/37965
RUN true
COPY --from=builder /opt/c2cgeoportal/geoportal/node_modules/ngeo/dist/* /etc/static-ngeo/
RUN rm /etc/static-ngeo/*.html
COPY --from=builder /etc/static-ngeo/* /etc/static-ngeo/
COPY --from=builder /app/alembic.ini /app/alembic.yaml ./
RUN chmod go+w /etc/static-ngeo/

RUN --mount=type=cache,target=/root/.cache \
    python3 -m pip install --disable-pip-version-check --editable=/app/ \
    && python3 -m compileall -q /venv/lib/python3.* \
        -x '/(ptvsd|.*pydev.*|networkx|scaffolds|yaml_include)/' \
    && python3 -m compileall -q "/app/{{cookiecutter.package}}_geoportal" -x "/app/{{cookiecutter.package}}_geoportal/static".* \
    && pip freeze > /requirements.txt \
    && chmod go+w "/app/{{cookiecutter.package}}_geoportal" "/app/{{cookiecutter.package}}_geoportal/authentication.py" "/app/{{cookiecutter.package}}_geoportal/multi_tenant.py" "/app/{{cookiecutter.package}}_geoportal/dev.py"

ARG GIT_HASH
RUN c2cwsgiutils-genversion ${GIT_HASH}

ARG PGSCHEMA
ENV PGSCHEMA=${PGSCHEMA}

ENTRYPOINT [ "/usr/bin/eval-templates" ]
CMD ["gunicorn", "--paste=/app/production.ini"]

ENV VISIBLE_ENTRY_POINT=/ \
    AUTHTKT_TIMEOUT=86400 \
    AUTHTKT_REISSUE_TIME=9000 \
    AUTHTKT_MAXAGE=86400 \
    AUTHTKT_COOKIENAME=auth_tkt \
    AUTHTKT_HTTP_ONLY=True \
    AUTHTKT_SECURE=True \
    AUTHTKT_SAMESITE=Lax \
    BASICAUTH=False \
    LOG_LEVEL=INFO \
    C2CGEOPORTAL_LOG_LEVEL=INFO \
    C2CWSGIUTILS_LOG_LEVEL=INFO \
    GUNICORN_LOG_LEVEL=INFO \
    SQL_LOG_LEVEL=WARNING \
    DOGPILECACHE_LOG_LEVEL=INFO \
    OTHER_LOG_LEVEL=WARNING \
    DEVELOPMENT=0 \
    LOG_TYPE=console
