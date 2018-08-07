# To install on system space
# Should be copy on /etc/systemd/system/

# To install on user space
# Should be copy on ~/.config/systemd/user/

[Unit]
Description=Docker Compose GeoMapFish Application Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${project_directory}
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
