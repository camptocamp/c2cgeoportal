FROM camptocamp/c2cwsgiutils:0
MAINTAINER Camptocamp "info@camptocamp.com"

RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ jessie-pgdg main" > /etc/apt/sources.list.d/postgres.list && \
    curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client-9.6 && \
    apt-get clean && \
    rm -r /var/lib/apt/lists/*

# Doing things in two steps to avoid needing to re-install everything when we do a rebuild
# after changing code

# Step #1 copy only the stuff needed to install the dependencies and run the script
WORKDIR /app

COPY admin/requirements.txt /app

RUN pip install --disable-pip-version-check --no-cache-dir \
    -e git://github.com/camptocamp/c2cgeoform.git@ce5ea9a7311fefbed32e1ad6bd22f4112faf65ad#egg=c2cgeoform \
    -r requirements.txt

EXPOSE 80

ENV APP_LOG_LEVEL=INFO \
    C2CWSGI_LOG_LEVEL=WARN \
    SQL_LOG_LEVEL=WARN \
    OTHER_LOG_LEVEL=WARN

# Provided by camptocamp/c2cwsgiutils:0
#ENV LOG_TYPE=console \
#    SQL_LOG_LEVEL=WARN \
#    OTHER_LOG_LEVEL=WARN \
#    DEVELOPMENT=0

ENV C2CWSGIUTILS_CONFIG=/app/docker.ini \
    DEVELOPMENT=1 \
    SQLALCHEMY_POOL_SIZE=5 \
    SQLALCHEMY_MAX_OVERFLOW=25

# Step #2 copy the rest of the files (watch for the .dockerignore)
COPY commons /commons
COPY admin /app

ARG GIT_HASH
ENV GIT_HASH=$GIT_HASH

RUN pip install --disable-pip-version-check --no-cache-dir -e ../commons

RUN pip install --disable-pip-version-check --no-cache-dir . && \
    /c2cwsgiutils/c2cwsgiutils_genversion.py $GIT_HASH && \
    flake8 acceptance_tests c2cgeoportal_admin *.py

ENTRYPOINT [ "/app/docker/docker-entrypoint.sh" ]
CMD [ "/c2cwsgiutils/c2cwsgiutils_run" ]
