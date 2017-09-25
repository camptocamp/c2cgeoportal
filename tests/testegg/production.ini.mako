[app:app]
use = egg:testegg
sqlalchemy.url = postgresql://${dbuser}:${dbpassword}@${dbhost}:${dbport}/${db}
mapserv.url = ${mapserv_url}
project = testegg
schema = main

[pipeline:main]
pipeline = app
