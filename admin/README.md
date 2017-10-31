# c2cgeoportal_admin

## Checkout

git clone git@github.com:camptocamp/c2cgeoportal.git
cd admin

## Run the application

### Set up the database
```
sudo -u postgres psql -c "CREATE USER \"www-data\" WITH PASSWORD 'www-data';"

DATABASE=c2cgeoportal
sudo -u postgres psql -c "CREATE DATABASE $DATABASE WITH OWNER \"www-data\";"
sudo -u postgres psql -d $DATABASE -c "CREATE EXTENSION postgis;"
```

Optionally update sqlachemy.url in development.ini

```
make init_db
```

### Run the development web server
```
make serve
```

## Run the tests

### Install the selenium gecko driver

### Create the test database
```
sudo -u postgres psql -c "CREATE USER \"www-data\" WITH PASSWORD 'www-data';"

DATABASE=c2cgeoportal_tests
sudo -u postgres psql -c "CREATE DATABASE $DATABASE WITH OWNER \"www-data\";"
sudo -u postgres psql -d $DATABASE -c "CREATE EXTENSION postgis;"
```

### Run the tests
```
make test
```

Open http://localhost:6543/user/
