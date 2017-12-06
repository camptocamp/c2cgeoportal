# c2cgeoportal_admin

## Run with docker

To build:
```
make docker-build
```

To build & run the application:
```
make docker-serve
```

Open http://localhost:8888/

The following views are also provided by `c2cwsgiutils`:
 * http://localhost:8888/versions.json
 * http://localhost:8888/stats.json
 * http://localhost:8888/health_check?max_level=3


## Run without docker


### Checkout

```
git clone git@github.com:camptocamp/c2cgeoportal.git
cd admin
```

### Set up the database
```
sudo -u postgres psql -c "CREATE USER \"www-data\" WITH PASSWORD 'www-data';"

DATABASE=c2cgeoportal
sudo -u postgres psql -c "CREATE DATABASE $DATABASE WITH OWNER \"www-data\";"
sudo -u postgres psql -d $DATABASE -c "CREATE EXTENSION postgis;"
```

Optionally update sqlachemy.url in development.ini or production.ini then:
```
make init_db
```

### Run the development web server
```
make serve
```

Open http://localhost:6543/users/

## Run the tests

### Install the selenium gecko driver

https://github.com/mozilla/geckodriver/releases

### Create the test database
```
sudo -u postgres psql -c "CREATE USER \"www-data\" WITH PASSWORD 'www-data';"

DATABASE=geomapfish_tests
sudo -u postgres psql -c "CREATE DATABASE $DATABASE WITH OWNER \"www-data\";"
sudo -u postgres psql -d $DATABASE -c "CREATE EXTENSION postgis;"
```

### Run the tests
```
make test
```
