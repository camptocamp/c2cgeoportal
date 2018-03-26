# c2cgeoportal_common

## Checkout

git clone git@github.com:camptocamp/c2cgeoportal.git
cd common

## Create virtual environment

make install

## Set up the tests database

```
sudo -u postgres psql -c "CREATE USER \"www-data\" WITH PASSWORD 'www-data';"

DATABASE=geomapfish_tests
sudo -u postgres psql -c "CREATE DATABASE $DATABASE WITH OWNER \"www-data\";"
sudo -u postgres psql -d $DATABASE -c "CREATE EXTENSION postgis;"

```
use common/testing/initialized.py to create the database (development.ini at admin side)

```

## Run the tests

```
make test
```
