FROM camptocamp/geomapfish-build:{{geomapfish_version}} as builder
LABEL maintainer Camptocamp "info@camptocamp.com"

ENV NODE_PATH=/usr/lib/node_modules

WORKDIR /app
COPY . /app

RUN make checks
RUN make build
RUN mv webpack.apps.js webpack.apps.js.tmpl && \
    ln --symbolic /usr/lib/node_modules/ .

ENTRYPOINT [ "/usr/bin/eval-templates" ]
CMD [ "webpack-dev-server", "--mode=development", "--debug", "--watch", "--progress", "--no-inline" ]

###############################################################################

FROM camptocamp/geomapfish:{{geomapfish_version}} as runner

WORKDIR /app
COPY . /app
COPY --from=builder /usr/lib/node_modules/ngeo/dist/* \
    /etc/static-ngeo/
COPY --from=builder /etc/static-ngeo/* /etc/static-ngeo/
COPY --from=builder /app/alembic.ini /app/alembic.yaml ./
RUN chmod go+w /etc/static-ngeo/ \
    /app/{{package}}_geoportal/static-ngeo/api/apihelp/ \
    /app/{{package}}_geoportal/locale/ \
    /app/{{package}}_geoportal/locale/*/LC_MESSAGES/{{package}}_geoportal-client.po

RUN pip install --disable-pip-version-check --no-cache-dir --no-deps --editable=/app/ && \
    python -m compileall -q /app/{{package}}_geoportal -x /app/{{package}}_geoportal/static.*

ARG GIT_HASH
RUN c2cwsgiutils_genversion.py $GIT_HASH

ENV LOG_LEVEL=INFO \
    GUNICORN_ACCESS_LOG_LEVEL=INFO \
    C2CGEOPORTAL_LOG_LEVEL=WARN

ENTRYPOINT [ "/usr/bin/eval-templates" ]
CMD ["c2cwsgiutils_run"]
