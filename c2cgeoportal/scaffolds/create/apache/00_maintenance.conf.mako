# Document Root est htdocs
RewriteEngine On
# Localhost
RewriteCond %{REMOTE_ADDR} !^127\.|::1
RewriteCond %{REMOTE_HOST} !^localhost
RewriteCond %{REMOTE_HOST} !^${host}
# Your IP
RewriteCond %{REMOTE_ADDR} !^192\.168\.1\.1
# Maintenance page
Alias /maintenance ${directory}/${package}/static/maintenance/

RewriteCond ${directory}/${package}/static/maintenance/maintenance.html -f
RewriteCond ${directory}/apache/maintenance.enable -f

RewriteCond %{SCRIPT_FILENAME} !maintenance/maintenance.html
# Enable this line if you want to use image in html page
# RewriteCond %{SCRIPT_FILENAME} !maintenance/maintenance.jpeg

RewriteRule ^.*$ /maintenance/maintenance.html [R=503,L]
ErrorDocument 503 /maintenance/maintenance.html
#Header Set Cache-Control "max-age=0, no-store"
