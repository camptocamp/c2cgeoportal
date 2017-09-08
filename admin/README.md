# c2cgeoportal_admin

## Checkout

git clone git@github.com:camptocamp/c2cgeoportal.git
cd admin

## Build the app

Install the virtual env, build the app:
```
make build
```

## Set up the database

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

## Run the application

```
make serve
```

## Build docker image


```
make build_admin
```
