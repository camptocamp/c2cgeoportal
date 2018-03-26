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

### Install the selenium chrome driver

https://sites.google.com/a/chromium.org/chromedriver/downloads

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

Note that you can run all tests but selenium ones (really fast):
```
.build/venv/bin/pytest -m "not selenium"
```
