FROM camptocamp/geomapfish-config-build:${geomapfish_version}

ARG PGSCHEMA
ENV PGSCHEMA=$PGSCHEMA

COPY . /tmp/config/

RUN mv /tmp/config/bin/* /usr/bin/ && \
    if [ -e /tmp/config/mapserver ]; then mv /tmp/config/mapserver /etc/; fi && \
    if [ -e /tmp/config/tilegeneration ]; then mv /tmp/config/tilegeneration /etc/; fi && \
    if [ -e /tmp/config/qgisserver ]; then mv /tmp/config/qgisserver /etc/qgisserver; fi && \
    if [ -e /tmp/config/mapcache ]; then mv /tmp/config/mapcache /etc/; fi && \
    if [ -e /tmp/config/front ]; then mv /tmp/config/front /etc/haproxy; fi && \
    if [ -e /tmp/config/front_dev ]; then mv /tmp/config/front_dev /etc/haproxy_dev; fi && \
    mkdir --parent /usr/local/tomcat/webapps/ROOT/ && \
    if [ -e /tmp/config/print ]; then mv /tmp/config/print/print-apps /usr/local/tomcat/webapps/ROOT/; fi && \
    chmod g+w -R /etc /usr/local/tomcat/webapps && \
    adduser www-data root

VOLUME /etc/mapserver \
    /etc/qgisserver \
    /etc/mapcache \
    /etc/tilegeneration \
    /usr/local/tomcat/webapps/ROOT/print-apps \
    /etc/haproxy_dev \
    /etc/haproxy

ENTRYPOINT [ "/usr/bin/entrypoint" ]
