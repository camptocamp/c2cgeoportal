#!groovy
@Library('c2c-pipeline-library')
import static com.camptocamp.utils.*

final MAIN_BRANCH = 'master'
env.MAIN_BRANCH = MAIN_BRANCH
final MAJOR_VERSION = '2.3'
env.MAJOR_VERSION = MAJOR_VERSION

def clean() {
    sh 'git clean -dx --force'

    sh 'docker ps --all | grep camptocamp/c2cgeoportal | awk \'{print($1)}\' | xargs --no-run-if-empty docker rm --volumes'
    sh 'docker ps --all | grep camptocamp/geomapfish | awk \'{print($1)}\' | xargs --no-run-if-empty docker rm --volumes'
    sh 'docker ps --all | grep camptocamp/testgeomapfish | awk \'{print($1)}\' | xargs --no-run-if-empty docker rm --volumes'
    sh 'docker volume ls | grep home-jenkins-slave-workspace | awk \'{print($2)}\' | xargs --no-run-if-empty docker volume rm'

    sh 'docker ps'
    sh 'docker ps --all --filter status=exited'
    sh 'docker volume ls'
}

dockerBuild {
    try {
        stage('Clean') {
            checkout scm
            sh 'docker --version'
            sh 'docker-compose --version'
            clean()
        }
        stage('Docker pull') {
            checkout scm
            sh 'make pull'
        }
        stage('Build build Docker image') {
            checkout scm
            sh "docker build --tag camptocamp/geomapfish-build-dev:${MAJOR_VERSION} docker/build"
        }
        stage('Build') {
            checkout scm
            sh './docker-run make clean-all'
            sh './docker-run travis/empty-make.sh help'
            sh './docker-run make build'
        }
        stage('Lint') {
            checkout scm
            sh 'bash -c "test \\"`./docker-run id`\\" == \\"uid=0(root) gid=0(root) groups=0(root)\\""'
            sh './docker-run make doc'
            sh './docker-run make geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot'
            sh './docker-run make admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot'
            // lint
            sh './docker-run make flake8'
            sh './docker-run make git-attributes'
            sh './docker-run make quote'
            sh './docker-run make spell'
            sh './docker-run travis/test-eof-newline'
            sh './docker-run travis/empty-make.sh build'
            // Test return code
            sh './docker-run true'
            sh 'if ./docker-run false; then false; fi'
            sh './docker-compose-run true'
            sh 'if ./docker-compose-run false; then false; fi'
        }
        stage('Build commons Docker image') {
            checkout scm
            sh "docker build --build-arg=MAJOR_VERSION=${MAJOR_VERSION} --tag camptocamp/geomapfish-commons:${MAJOR_VERSION} commons"
            sh "./docker-run --image=camptocamp/geomapfish-commons grep ${MAJOR_VERSION} /opt/c2cgeoportal_commons/c2cgeoportal_commons.egg-info/PKG-INFO"
        }
        stage('Build geoportal Docker image') {
            checkout scm
            sh "docker build --build-arg=MAJOR_VERSION=${MAJOR_VERSION} --tag camptocamp/geomapfish-build:${MAJOR_VERSION} geoportal"
            sh "./docker-run --image=camptocamp/geomapfish-build grep ${MAJOR_VERSION} /opt/c2cgeoportal_geoportal/c2cgeoportal_geoportal.egg-info/PKG-INFO"
        }

        stage('Test c2cgeoportal') {
            checkout scm
            sh '''./docker-run make docker-compose.yaml \
                geoportal/tests/functional/alembic.ini \
                docker/test-mapserver/mapserver.map prepare-tests'''
            try {
                sh './docker-compose-run sleep 15'
                sh './docker-compose-run alembic --config=geoportal/tests/functional/alembic.ini --name=main upgrade head'
                sh './docker-compose-run alembic --config=geoportal/tests/functional/alembic.ini --name=static upgrade head'
                sh './docker-compose-run make tests'
            } finally {
                sh 'docker-compose down'
            }
        }
        stage('Test Docker app') {
            checkout scm
            sh 'git config --global user.email travis@camptocamp.com'
            sh 'git config --global user.name Travis'
            sh 'rm -rf ${HOME}/workspace/testgeomapfish'
            sh 'docker build --tag=external-db docker/test-external-db'
            sh 'travis/create-new-project.sh ${HOME}/workspace'
            sh 'travis/run-on.sh ${HOME}/workspace/testgeomapfish/ ./docker-run travis/empty-make.sh --makefile=travis.mk help'
            sh 'travis/run-on.sh ${HOME}/workspace/testgeomapfish/ ./docker-run make --makefile=travis.mk build'
            try {
                sh 'travis/run-on.sh ${HOME}/workspace/testgeomapfish/ docker-compose up -d'
                sh './docker-run travis/waitwsgi http://`netstat --route --numeric|grep ^0.0.0.0|awk \'{print($2)}\'`:8080/'
                for (path in ['c2c/health_check', 'c2c/health_check?max_level=100', 'layers/test/values/type enum']) {
                    def start = sh(returnStdout: true, script: 'date --iso-8601=ns').trim()
                    try {
                        sh 'travis/test-new-project http://`netstat --route --numeric|grep ^0.0.0.0|awk \'{print($2)}\'`:8080/' + path
                    } catch (Exception error) {
                        sh "travis/run-on.sh ${HOME}/workspace/testgeomapfish/ docker-compose logs --since ${start}"
                        throw error
                    }
                }
            } finally {
                sh 'travis/run-on.sh ${HOME}/workspace/testgeomapfish/ docker-compose down'
            }
            sh 'travis/run-on.sh ${HOME}/workspace/testgeomapfish/ ./docker-run travis/empty-make.sh --makefile=travis.mk build'
            sh 'travis/run-on.sh ${HOME}/workspace/testgeomapfish/ ./docker-run make --makefile=travis.mk checks'
            sh '''find \
                ${HOME}/workspace/testgeomapfish/geoportal/setup.py \
                ${HOME}/workspace/testgeomapfish/geoportal/testgeomapfish_geoportal/*.py \
                ${HOME}/workspace/testgeomapfish/geoportal/testgeomapfish_geoportal/views \
                ${HOME}/workspace/testgeomapfish/commons/setup.py ${HOME}/workspace/testgeomapfish/commons/testgeomapfish_commons \
                -name \\*.py | xargs travis/squote'''
            sh 'travis/run-on.sh ${HOME}/workspace/testgeomapfish/ ./docker-run travis/status.sh'
            sh 'travis/run-on.sh ${HOME}/workspace/testgeomapfish/ ./docker-run make --makefile=empty-vars.mk geoportal/config.yaml'
            sh 'travis/run-on.sh ${HOME}/workspace/testgeomapfish/ ./docker-run make --makefile=travis.mk alembic.ini'
            sh 'travis/run-on.sh ${HOME}/workspace/testgeomapfish/ ./docker-compose-run sleep 15'
            sh 'travis/run-on.sh ${HOME}/workspace/testgeomapfish/ ./docker-compose-run alembic --name=main upgrade head'
            sh 'travis/run-on.sh ${HOME}/workspace/testgeomapfish/ ./docker-compose-run alembic --name=static upgrade head'
            sh 'travis/run-on.sh ${HOME}/workspace/testgeomapfish/ ./docker-compose-run alembic --name=static downgrade base'
            sh 'travis/run-on.sh ${HOME}/workspace/testgeomapfish/ ./docker-compose-run alembic --name=main downgrade base'
            sh 'rm -rf ${HOME}/workspacetestgeomapfish'
        }
        stage('Tests upgrades') {
            checkout scm
            // database for the GeoMapFish application
            sh 'docker build --tag=camptocamp/c2cgeoportal-gis-db docker/gis-db'
            try {
                sh 'docker run --name geomapfish-db --env=POSTGRES_USER=www-data --env=POSTGRES_PASSWORD=www-data --env=POSTGRES_DB=geomapfish --publish=5432:5432 --detach camptocamp/c2cgeoportal-gis-db'
                // Test Upgrade an convert project
                sh 'travis/test-upgrade-convert.sh init ${HOME}/workspace'
                parallel 'docker': {
                    sh 'travis/test-upgrade-convert.sh docker ${HOME}/workspace'
                    sh 'travis/test-upgrade-convert.sh tonondocker ${HOME}/workspace'
                }, 'nondocker': {
                    sh 'travis/test-upgrade-convert.sh nondocker ${HOME}/workspace'
                    sh 'travis/test-upgrade-convert.sh todocker ${HOME}/workspace'
                }, 'v220 docker': {
                    sh 'travis/test-upgrade-convert.sh v220-todocker ${HOME}/workspace'
                }, 'v220 nondocker': {
                    sh 'travis/test-upgrade-convert.sh v220-nontodocker ${HOME}/workspace'
                }
                sh 'travis/test-upgrade-convert.sh cleanup ${HOME}/workspace'
            } finally {
                sh 'docker stop geomapfish-db'
                sh 'docker rm --volumes geomapfish-db'
            }
        }
    } finally {
        stage('Clean') {
            checkout scm
            clean()
        }
    }
}
