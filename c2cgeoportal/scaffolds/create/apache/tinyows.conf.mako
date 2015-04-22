# to enable TinyOWS uncomment the following lines

# ScriptAlias /${instanceid}/tinyows /usr/lib/cgi-bin/tinyows
# <Location /${instanceid}/tinyows>
#   SetEnv TINYOWS_CONFIG_FILE ${directory}/mapserver/tinyows.xml
#
#   # restrict access to localhost so that all requests go through the proxy
#   Options All
#   Order deny,allow
#   Deny from all
#   Allow from 127.0.0.1 ::1
# </Location>
