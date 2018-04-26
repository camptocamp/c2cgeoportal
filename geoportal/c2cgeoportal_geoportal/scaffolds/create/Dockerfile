FROM tianon/true:latest
LABEL maintainer Camptocamp "info@camptocamp.com"

COPY mapserver /etc/mapserver
VOLUME /etc/mapserver

#COPY qgisserver /project
#VOLUME /project

COPY mapcache /mapcache
VOLUME /mapcache

COPY tilegeneration /tilecloudchain
VOLUME /tilecloudchain

COPY print/print-apps /usr/local/tomcat/webapps/ROOT/print-apps
VOLUME /usr/local/tomcat/webapps/ROOT/print-apps

COPY front /etc/haproxy
VOLUME /etc/haproxy
