ARG {{cookiecutter.geomapfish_version_tag}}
ARG {{cookiecutter.geomapfish_major_version_tag}}

FROM camptocamp/geomapfish-tools:{{cookiecutter.geomapfish_version_tag_env}} AS builder

ENV VARS_FILE=vars.yaml
ENV CONFIG_VARS sqlalchemy.url sqlalchemy.pool_recycle sqlalchemy.pool_size sqlalchemy.max_overflow \
    sqlalchemy.executemany_mode sqlalchemy_slave.url sqlalchemy_slave.pool_recycle sqlalchemy_slave.pool_size \
    sqlalchemy_slave.max_overflow sqlalchemy_slave.executemany_mode schema schema_static enable_admin_interface \
    default_locale_name servers layers cache admin_interface getitfixed functionalities \
    raster shortener hide_capabilities tinyowsproxy resourceproxy print_url print_get_redirect \
    checker check_collector default_max_age package srid \
    reset_password fulltextsearch global_headers headers authorized_referers hooks stats db_chooser \
    dbsessions urllogin host_forward_host headers_whitelist headers_blacklist \
    smtp c2c.base_path welcome_email \
    lingva_extractor interfaces_config interfaces devserver_url api authentication intranet metrics pdfreport \
    vector_tiles i18next main_ogc_server static_files http_options

COPY . /tmp/config/

ARG SIMPLE
ENV SIMPLE=$SIMPLE

RUN build-l10n "{{cookiecutter.package}}"

ARG PGSCHEMA
ENV PGSCHEMA=$PGSCHEMA

RUN \
    cd /tmp/config/geoportal/ \
    && [ "${SIMPLE}" == "TRUE" ] || rm -f {{cookiecutter.package}}_geoportal/*.py \
    && c2c-template --vars ${VARS_FILE} \
        --get-config {{cookiecutter.package}}_geoportal/config.yaml \
        ${CONFIG_VARS} \
    && pykwalify --data-file {{cookiecutter.package}}_geoportal/config.yaml \
        --schema-file CONST_config-schema.yaml \
    && rm CONST_* vars.yaml \
    && qgisserver-plugin-config {{cookiecutter.package}}_geoportal/config.yaml ../qgisserver/geomapfish.yaml.tmpl

###############################################################################

FROM camptocamp/geomapfish-config:{{cookiecutter.geomapfish_major_version_tag_env}} AS gmf_config

ARG PGSCHEMA
ENV PGSCHEMA=$PGSCHEMA

COPY --from=builder /tmp/config/ /tmp/config/

RUN \
    mvif /tmp/config/mapserver /etc/ \
    && mvif /tmp/config/tilegeneration /etc/ \
    && mvif /tmp/config/qgisserver /etc/qgisserver \
    && mvif /tmp/config/haproxy/* /etc/haproxy/ \
    && mkdir --parent /usr/local/tomcat/webapps/ROOT/ \
    && mvif /tmp/config/print /tmp/config/print/print-apps /usr/local/tomcat/webapps/ROOT/ \
    && mv /tmp/config/geoportal/{{cookiecutter.package}}_geoportal/ /etc/geomapfish/ \
    && ( mv /tmp/config/geoportal/* /etc/geomapfish/ || true ) \
    && chmod g+w -R \
        /etc/geomapfish \
        /etc/mapserver \
        /etc/qgisserver \
        /etc/tilegeneration \
        /usr/local/tomcat/webapps/ROOT/print-apps \
        /etc/haproxy_dev \
        /etc/haproxy \
    && sed 's#bind :80#bind *:443 ssl crt /etc/haproxy_dev/localhost.pem#g' /etc/haproxy/haproxy.cfg.tmpl \
        > /etc/haproxy_dev/haproxy.cfg.tmpl \
    && echo '    http-request set-header X-Forwarded-Proto https' >> /etc/haproxy_dev/haproxy.cfg.tmpl

VOLUME /etc/geomapfish \
    /etc/mapserver \
    /etc/qgisserver \
    /etc/tilegeneration \
    /usr/local/tomcat/webapps/ROOT/print-apps \
    /etc/haproxy_dev \
    /etc/haproxy
