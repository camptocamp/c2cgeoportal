FROM camptocamp/geomapfish-build:${geomapfish_version}
LABEL maintainer Camptocamp "info@camptocamp.com"

ENV NODE_PATH=/usr/lib/node_modules \
    LOG_LEVEL=INFO \
    GUNICORN_ACCESS_LOG_LEVEL=INFO \
    C2CGEOPORTAL_LOG_LEVEL=WARN \
    PGHOST=db \
    PGHOST_SLAVE=db \
    PGPORT=5432 \
    PGUSER=www-data \
    PGPASSWORD=www-data \
    PGDATABASE=geomapfish \
    PGSCHEMA=main \
    PGSCHEMA_STATIC=main_static \
    VISIBLE_ENTRY_POINT=/ \
    TINYOWS_URL=http://tinyows/ \
    MAPSERVER_URL=http://mapserver/ \
    PRINT_URL=http://print:8080/print/ \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /app
COPY . /app

RUN mv webpack.apps.js webpack.apps.js.tmpl && \
    ln --symbolic /usr/lib/node_modules/ . && \
    chmod g+w -R . && \
    adduser www-data root

ARG GIT_HASH

RUN pip install --disable-pip-version-check --no-cache-dir --no-deps --editable=/app/ && \
    python -m compileall -q /app/${package}_geoportal -x /app/${package}_geoportal/static.* && \
    c2cwsgiutils_genversion.py $GIT_HASH

ENTRYPOINT [ "/usr/bin/eval-templates" ]
CMD ["c2cwsgiutils_run"]
