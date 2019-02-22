<Location /${instanceid}/wsgi/>
    # Zip resources
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css application/x-javascript text/javascript application/javascript application/json application/vnd.ogc.wms_xml application/vnd.ogc.gml application/vnd.ogc.se_xml
</Location>

<LocationMatch /${instanceid}/wsgi/(proj|static)>
    # Instruct proxys that these files are cacheable.
    Header merge Cache-Control "public"
</LocationMatch>

<Location /${instanceid}/tiles/>
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css application/x-javascript text/javascript application/javascript application/xml
    Header set Access-Control-Allow-Origin "*"
    Header set Access-Control-Allow-Headers "Content-Type"
    Header merge Cache-Control "public"
    ProxyPreserveHost Off
</Location>

<LocationMatch /${instanceid}/mapcache/>
    # Instructs to set CORS on mapcache tiles
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css application/x-javascript text/javascript application/javascript application/xml
    Header set Access-Control-Allow-Origin "*"
    Header set Access-Control-Allow-Headers "Content-Type"
    Header merge Cache-Control "public"
    ProxyPreserveHost Off
</LocationMatch>

<LocationMatch /${instanceid}/mapcache/>
    # Instructs to set CORS on mapcache tiles
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css application/x-javascript text/javascript application/javascript application/xml
    Header set Access-Control-Allow-Origin "*"
    Header set Access-Control-Allow-Headers "Content-Type"
    Header merge Cache-Control "public"
</LocationMatch>
