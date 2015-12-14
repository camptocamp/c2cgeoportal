FROM grahamdumpleton/mod-wsgi-docker:python-2.7
MAINTAINER Camptocamp "info@camptocamp.com"

# Doing things in two steps to avoid needing to re-install everything when we do a rebuild
# after changing code

# Step #1 copy only the stuff needed to install the dependencies and run the script
COPY *.txt setup.py /app/
COPY .whiskey /app/.whiskey
RUN mod_wsgi-docker-build

# Step #2 copy the rest of the files (watch for the .dockerignore
COPY . /app

EXPOSE 80

CMD ["mod_wsgi-docker-start", "apache/application.wsgi"]
