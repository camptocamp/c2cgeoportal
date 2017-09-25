<tinyows
    online_resource="http://${host}/${instanceid}/wsgi/tinyows_proxy"
    schema_dir="/usr/share/tinyows/schema/"
    log="tinyows.log"
    log_level="1"
    check_schema="0">

  <contact
      name="GeoMapFish"
      site="http://www.geomapfish.org/"
      email="geomapfish@googlegroups.com" />

  <metadata
      name="GeoMapFish TinyOWS Server"
      title="GeoMapFish TinyOWS Server" />

  <pg
      host="${dbhost}"
      user="${dbuser}"
      password="${dbpassword}"
      port="${dbport}"
      dbname="${db}" />

<!--
  <layer
      retrievable="1"
      writable="1"
      ns_prefix="tows"
      ns_uri="http://www.tinyows.org/"
      name="point"
      schema="edit"
      table="point"
      title="Points"
      pkey="id" />
-->
</tinyows>
