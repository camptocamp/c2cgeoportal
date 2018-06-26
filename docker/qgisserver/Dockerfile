FROM camptocamp/qgis-server:latest
LABEL maintainer Camptocamp "info@camptocamp.com"

COPY __init__.py accesscontrol.py metadata.txt /var/www/plugins/geomapfish_qgisserver/
COPY commons /opt/c2cgeoportal_commons

RUN python3 -m pip install --editable /opt/c2cgeoportal_commons
