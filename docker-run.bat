SET SRC_DIR=/c/Users/ochriste/test/c2cgeoportal
SET TEMP_DIR=/c/temp
SET DOCKER_ARG=
SET DOCKER_ADRS=192.168.99.100
SET USERNAME=C2cgeoportail
SET USER_ID=1000
SET GROUP_ID=1000

docker run ^
    %DOCKER_ARG% ^
    --volume=%SRC_DIR%/build:/build ^
    --volume=%SRC_DIR%:/src ^
    --volume=home:/home/%USERNAME% ^
    --volume=%TEMP_DIR%/testgeomapfish:/tmp/travis/testgeomapfish ^
    --add-host=db:%DOCKER_ADRS% ^
    --add-host=mapserver:%DOCKER_ADRS% ^
    --env=HOME=/home/%USERNAME% ^
    --env=USER_NAME=%USERNAME% ^
    --env=USER_ID=%USER_ID% ^
    --env=GROUP_ID=%GROUP_ID% ^
    camptocamp/geomapfish_build_dev ^
    run "%*"
