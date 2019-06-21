FROM camptocamp/geomapfish-config-build:{{geomapfish_version}}

ARG PGSCHEMA
ENV PGSCHEMA=$PGSCHEMA

COPY . /tmp/config/

ENV CONFIG_VARS sqlalchemy.url sqlalchemy.pool_recycle sqlalchemy.pool_size sqlalchemy.max_overflow \
    sqlalchemy.use_batch_mode sqlalchemy_slave.url sqlalchemy_slave.pool_recycle sqlalchemy_slave.pool_size \
    sqlalchemy_slave.max_overflow sqlalchemy_slave.use_batch_mode schema schema_static enable_admin_interface \
    default_locale_name servers layers available_locale_names cache admin_interface functionalities \
    raster shortener hide_capabilities tinyowsproxy resourceproxy print_url print_get_redirect \
    checker check_collector default_max_age package srid \
    reset_password fulltextsearch global_headers headers authorized_referers hooks stats db_chooser \
    dbsessions urllogin host_forward_host smtp c2c.base_path welcome_email \
    lingua_extractor interfaces_config interfaces devserver_url api
ENV VARS_FILE=vars.yaml

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
    cd /tmp/config/geoportal && \
    mkdir --parent /etc/geomapfish/ && \
    c2c-template --vars ${VARS_FILE} --get-config /tmp/_config.yaml ${CONFIG_VARS} && \
    pykwalify --data-file /tmp/_config.yaml --schema-file CONST_config-schema.yaml && \
    mv /tmp/_config.yaml /etc/geomapfish/config.yaml && \
    adduser www-data root

VOLUME /etc/geomapfish \
    /etc/mapserver \
    /etc/qgisserver \
    /etc/mapcache \
    /etc/tilegeneration \
    /usr/local/tomcat/webapps/ROOT/print-apps \
    /etc/haproxy_dev \
    /etc/haproxy

ENTRYPOINT [ "/usr/bin/entrypoint" ]
