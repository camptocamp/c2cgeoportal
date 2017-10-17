FROM camptocamp/${package}-commons:${docker_tag}
LABEL maintainer Camptocamp "info@camptocamp.com"

COPY . /app
WORKDIR /app

ARG GIT_HASH

RUN pip install --disable-pip-version-check --no-cache-dir --no-deps --editable=/app/ && \
    c2cwsgiutils_genversion.py $GIT_HASH

ENTRYPOINT []
CMD ["c2cwsgiutils_run"]
