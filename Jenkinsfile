#!groovy
@Library('c2c-pipeline-library')
import static com.camptocamp.utils.*

final MAIN_BRANCH = 'master'
env.MAIN_BRANCH = MAIN_BRANCH
final MAJOR_VERSION = '2.3'
env.MAJOR_VERSION = MAJOR_VERSION
env.CI = 'true'

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

timeout(time: 2, unit: 'HOURS') {
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
                sh 'make pull-base'
            }
            stage('Build build Docker image') {
                checkout scm
                sh "docker build --tag camptocamp/geomapfish-build-dev:${MAJOR_VERSION} docker/build"
            }
            stage('Build') {
                checkout scm
                sh './docker-run make clean-all'
                sh './docker-run travis/empty-make help'
                sh './docker-run make build'
                sh './docker-run travis/status.sh'
            }
            stage('Lint') {
                checkout scm
                sh 'bash -c "test \\"`./docker-run id`\\" == \\"uid=0(root) gid=0(root) groups=0(root)\\""'
                sh './docker-run travis/empty-make build'
                sh './docker-run make doc'
                sh './docker-run make geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot'
                sh './docker-run make admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot'
                // lint
                sh './docker-run make flake8'
                sh './docker-run make mypy'
                sh './docker-run make git-attributes'
                sh './docker-run make quote'
                sh './docker-run make spell'
                sh './docker-run travis/status.sh'
                sh './docker-run travis/test-eof-newline'
                // Test return code
                sh './docker-run true'
                sh 'if ./docker-run false; then false; fi'
                try {
                    sh './docker-compose-run true'
                    sh 'if ./docker-compose-run false; then false; fi'
                } catch (Exception error) {
                    sh 'docker-compose logs'
                    throw error
                } finally {
                    sh 'docker-compose down'
                }
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
                    sh './docker-compose-run alembic --config=geoportal/tests/functional/alembic.ini --name=main upgrade head'
                    sh './docker-compose-run alembic --config=geoportal/tests/functional/alembic.ini --name=static upgrade head'
                    sh './docker-compose-run make tests'
                } catch (Exception error) {
                    sh 'docker-compose logs'
                    throw error
                } finally {
                    sh 'docker-compose down'
                }
                sh './docker-run travis/codacy.sh'
            }
            stage('Test Docker app') {
                checkout scm
                sh 'rm -rf ${HOME}/workspace/testgeomapfish'
                sh 'docker build --tag=camptocamp/testgeomapfish-external-db:latest docker/test-external-db'
                try {
                    sh 'travis/create-new-project.sh ${HOME}/workspace'
                    sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ ./docker-compose-run make update-po'
                } catch (Exception error) {
                    sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ docker-compose --file=docker-compose-build.yaml logs'
                    throw error
                } finally {
                    // down will lost the default theme
                    sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ docker-compose --file=docker-compose-build.yaml stop'
                }
                // Commit the l10n files modifications
                // To prevent fail on modification files check
                sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ git add geoportal/testgeomapfish_geoportal/locale/*/LC_MESSAGES/testgeomapfish_geoportal-*.po'
                sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ git commit -m "Upgrade the po files"'
                sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ ./docker-run travis/empty-make --makefile=travis.mk help'
                sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ ./docker-run make --makefile=travis.mk build'
                sh 'cat ${HOME}/workspace/testgeomapfish/testdb/*.sql'
                sh 'cat ${HOME}/workspace/testgeomapfish/geoportal/config.yaml'
                try {
                    sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ docker-compose up -d'
                    sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ docker-compose exec -T geoportal wait-for-db'
                    sh './docker-run travis/waitwsgi http://`netstat --route --numeric|grep ^0.0.0.0|awk \'{print($2)}\'`:8080/'
                    for (path in ['c2c/health_check', 'c2c/health_check?max_level=100', 'layers/test/values/type enum']) {
                        def start_lines = [:]
                        ['db', 'external-db', 'print', 'mapserver', 'geoportal'].each { service ->
                            def start_line = sh(returnStdout: true, script: "travis/run-on ${HOME}/workspace/testgeomapfish/ docker-compose logs ${service} | wc -l") as Integer
                            start_lines.service = start_line
                        }
                        try {
                            sh 'travis/test-new-project http://`netstat --route --numeric|grep ^0.0.0.0|awk \'{print($2)}\'`:8080/' + path
                        } catch (Exception error) {
                            ['db', 'external-db', 'print', 'mapserver', 'geoportal'].each { service ->
                                def end_line = sh(returnStdout: true, script: "travis/run-on ${HOME}/workspace/testgeomapfish/ docker-compose logs ${service} | wc -l") as Integer
                                sh "travis/run-on ${HOME}/workspace/testgeomapfish/ docker-compose logs --timestamps --tail=${Math.max(1, end_line - start_lines.service)} ${service}"
                            }
                            throw error
                        }
                    }
                } catch (Exception error) {
                    sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ docker-compose logs --timestamps'
                    throw error
                } finally {
                    sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ docker-compose down'
                }
                sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ ./docker-run travis/empty-make --makefile=travis.mk build'
                sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ ./docker-run make --makefile=travis.mk checks'
                sh '''find \
                    ${HOME}/workspace/testgeomapfish/geoportal/setup.py \
                    ${HOME}/workspace/testgeomapfish/geoportal/testgeomapfish_geoportal/*.py \
                    ${HOME}/workspace/testgeomapfish/geoportal/testgeomapfish_geoportal/views \
                    ${HOME}/workspace/testgeomapfish/commons/setup.py \
                    ${HOME}/workspace/testgeomapfish/commons/testgeomapfish_commons \
                    -name \\*.py | xargs travis/squote'''
                sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ ./docker-run travis/status.sh'
                sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ ./docker-run make --makefile=empty-vars.mk geoportal/config.yaml'
                sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ ./docker-run make --makefile=travis.mk alembic.ini'
                try {
                    sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ ./docker-compose-run alembic --name=main upgrade head'
                    sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ ./docker-compose-run alembic --name=static upgrade head'
                    sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ ./docker-compose-run alembic --name=static downgrade base'
                    sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ ./docker-compose-run alembic --name=main downgrade base'
                } catch (Exception error) {
                    sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ docker-compose --file=docker-compose-build.yaml logs'
                    throw error
                } finally {
                    sh 'travis/run-on ${HOME}/workspace/testgeomapfish/ docker-compose --file=docker-compose-build.yaml down'
                }
                sh 'rm -rf ${HOME}/workspace/testgeomapfish'
            }
            stage('Tests upgrades') {
                checkout scm
                try {
                    sh 'docker run --name geomapfish-db --env=POSTGRES_USER=www-data --env=POSTGRES_PASSWORD=www-data --env=POSTGRES_DB=geomapfish --publish=5432:5432 --detach camptocamp/geomapfish-test-db'
                    // Test Upgrade an convert project
                    sh 'travis/test-upgrade-convert.sh init ${HOME}/workspace'
                    sh 'travis/test-upgrade-convert.sh v220-todocker ${HOME}/workspace'
                    /*parallel 'docker': {
                        sh 'travis/test-upgrade-convert.sh docker ${HOME}/workspace'
                        sh 'travis/test-upgrade-convert.sh tonondocker ${HOME}/workspace'
                    }, 'nondocker': {
                        sh 'travis/test-upgrade-convert.sh nondocker ${HOME}/workspace'
                        sh 'travis/test-upgrade-convert.sh todocker ${HOME}/workspace'
                    }, 'v220 docker': {
                        sh 'travis/test-upgrade-convert.sh v220-todocker ${HOME}/workspace'
                    }, 'v220 nondocker': {
                        sh 'travis/test-upgrade-convert.sh v220-tonondocker ${HOME}/workspace'
                    }*/
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
}
