version: '2'
services:
  config:
    image: ${docker_base}-globalconfig:${docker_tag}

  nginx:
    image: nginx:1
    ports:
      - 8081:80
    volumes_from:
      - config:ro
