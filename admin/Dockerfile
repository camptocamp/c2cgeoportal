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
COPY *.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

ENV C2CWSGI_LOG_LEVEL=INFO


#ENV SQLALCHEMY_POOL_SIZE=5 \
#    SQLALCHEMY_MAX_OVERFLOW=25

#those have default values, but need to be there empty for the substitution in production.ini to work
#ENV OP_AUTH_URL="" \
#    OP_TOKEN_URL="" \
#    OP_USERINFO_URL="" \
#    OP_LOGOUT_URL=""

# Step #2 copy the rest of the files (watch for the .dockerignore)
COPY . /app

ARG GIT_HASH
ENV GIT_HASH=$GIT_HASH

RUN python /app/setup.py install && \
    flake8 /app/acceptance_tests /app/c2cgeoportal_admin /app/*.py && \
    c2cwsgiutils_genversion.py $GIT_HASH
