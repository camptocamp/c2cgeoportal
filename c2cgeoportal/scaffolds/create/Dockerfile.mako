FROM camptocamp/geomapfish_build:${geomapfish_version}
LABEL maintainer Camptocamp "info@camptocamp.com"

COPY . /app
RUN pip install --disable-pip-version-check --no-cache-dir --no-deps --editable /app/

EXPOSE 80

ENTRYPOINT ["/app/gunicorn-run"]
