# c2cgeoportal_admin

## Run with docker

To build:
```
make build_admin
```

To build & run the application:
```
make run_admin
```

Open http://localhost:8888/

The following views are also provided by `c2cwsgiutils`:
 * http://localhost:8888/versions.json
 * http://localhost:8888/stats.json
 * http://localhost:8888/health_check?max_level=3


## Run without docker


### Checkout

git clone --recursive git@github.com:camptocamp/c2cgeoportal.git
cd admin

### Build the app

Install the virtual env, build the app:
```
make build
```

### Set up the database

```
sudo -u postgres psql -c "CREATE USER \"www-data\" WITH PASSWORD 'www-data';"

DATABASE=c2cgeoportal
sudo -u postgres psql -c "CREATE DATABASE $DATABASE WITH OWNER \"www-data\";"
sudo -u postgres psql -d $DATABASE -c "CREATE EXTENSION postgis;"
```

Optionally update sqlachemy.url in production.ini

```
make init_db
```

## Run the tests

```
make test
```