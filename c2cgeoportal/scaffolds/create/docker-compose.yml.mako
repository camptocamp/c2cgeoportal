# A compose file for development.
% if dbhost == "db":
db:
  build: testDB
  environment:
    POSTGRES_PASSWORD: ${dbpassword}
  #ports:
  #  - 15432:5432
%endif

print:
  image: ${docker_base}_print:latest
  links:
    - mapserver
  #ports:
  #  - 8280:8080

mapserver:
  image: ${docker_base}_mapserver:latest
% if dbhost == "db":
  links:
    - db
% endif
  #ports:
  #  - 8380:80

wsgi:
  image: ${docker_base}_wsgi:latest
  links:
    - mapserver
% if dbhost == "db":
    - db
% endif
  ports:
    - 8480:80
