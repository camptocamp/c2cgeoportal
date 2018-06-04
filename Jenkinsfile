#!groovy
@Library('c2c-pipeline-library')
import static com.camptocamp.utils.*

final MAIN_BRANCH = '2.3'
env.MAIN_BRANCH = MAIN_BRANCH
final MAJOR_VERSION = '2.3'
env.MAJOR_VERSION = MAJOR_VERSION
env.CI = 'true'

def clean() {
    sh 'git clean -dx --force'

    sh 'docker ps --all | grep camptocamp/c2cgeoportal | awk \'{print($1)}\' | xargs --no-run-if-empty docker rm --force --volumes'
    sh 'docker ps --all | grep camptocamp/geomapfish | awk \'{print($1)}\' | xargs --no-run-if-empty docker rm --force --volumes'
    sh 'docker ps --all | grep camptocamp/testgeomapfish | awk \'{print($1)}\' | xargs --no-run-if-empty docker rm --force --volumes'
    sh 'docker volume ls | grep home-jenkins-slave-workspace | awk \'{print($2)}\' | xargs --no-run-if-empty docker volume rm'

    sh 'docker ps'
    sh 'docker ps --all --filter status=exited'
    sh 'docker volume ls'

    sh 'travis/test-upgrade-convert.sh cleanup ${HOME}/workspace'
    sh 'rm -rf ${HOME}/workspace/testgeomapfish'
}

dockerBuild {
    timeout(time: 2, unit: 'HOURS') {
        try {
            stage('Clean') {
                checkout scm
                sh 'docker --version'
                sh 'docker-compose --version'
                clean()
            }
            stage('Build') {
                checkout scm
                sh 'make docker-build'
            }
            stage('Tests') {
                checkout scm
                parallel 'Lint and test c2cgeoportal': {
                    sh './docker-run travis/status.sh'
                    sh './docker-run travis/empty-make help'
                    sh 'bash -c "test \\"`./docker-run id`\\" == \\"uid=0(root) gid=0(root) groups=0(root)\\""'
                    sh './docker-run travis/short-make build'
                    sh './docker-run make doc'
                    // lint
                    sh './docker-run make checks'
                    sh './docker-run travis/status.sh'
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

                    sh './docker-run make prepare-tests'
                    sh './docker-run travis/status.sh'
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
                    sh './docker-run travis/status.sh'
                }, 'Test Docker app': {
                    sh 'rm -rf ${HOME}/workspace/testgeomapfish'
                    sh 'docker build --tag=camptocamp/testgeomapfish-external-db:latest docker/test-external-db'
                    try {
                        sh 'travis/create-new-project.sh ${HOME}/workspace'
                        sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-compose-run make update-po)'
                    } catch (Exception error) {
                        sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose --file=docker-compose-build.yaml logs)'
                        throw error
                    } finally {
                        // down will lost the default theme
                        sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose --file=docker-compose-build.yaml stop)'
                    }
                    // Commit the l10n files modifications
                    // To prevent fail on modification files check
                    sh '(cd ${HOME}/workspace/testgeomapfish/; git add geoportal/testgeomapfish_geoportal/locale/*/LC_MESSAGES/testgeomapfish_geoportal-*.po)'
                    sh '(cd ${HOME}/workspace/testgeomapfish/; git commit -m "Upgrade the po files")'
                    sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-run travis/empty-make --makefile=travis.mk help)'
                    sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-run make --makefile=travis.mk build)'
                    sh 'cat ${HOME}/workspace/testgeomapfish/testdb/*.sql'
                    sh 'cat ${HOME}/workspace/testgeomapfish/geoportal/config.yaml'
                    withCredentials([[
                        $class: 'UsernamePasswordMultiBinding',
                        credentialsId: 'dockerhub',
                        usernameVariable: 'USERNAME',
                        passwordVariable: 'PASSWORD'
                    ]]) {
                        try {
                            sh 'docker login -u "$USERNAME" -p "$PASSWORD"'
                            sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose up --force-recreate -d)'
                            sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose exec -T geoportal wait-for-db)'
                            sh './docker-run travis/waitwsgi http://`netstat --route --numeric|grep ^0.0.0.0|awk \'{print($2)}\'`:8080/'
                            for (path in [
                                'c2c/health_check',
                                'c2c/health_check?max_level=9',
                                'c2c/health_check?checks=check_collector',
// TODO: activate gunicon logs to debug this test
//                                'layers/test/values/type enum',
                                'admin/layertree',
                                'admin/layertree/children'
                            ]) {
                                def start_lines = [:]
                                ['db', 'external-db', 'print', 'mapserver', 'geoportal'].each { service ->
                                    def start_line = sh(returnStdout: true, script: "(cd ${HOME}/workspace/testgeomapfish/; docker-compose logs ${service}) | wc -l") as Integer
                                    start_lines.service = start_line
                                }
                                try {
                                    sh 'travis/test-new-project http://`netstat --route --numeric|grep ^0.0.0.0|awk \'{print($2)}\'`:8080/' + path
                                } catch (Exception error) {
                                    ['db', 'external-db', 'print', 'mapserver', 'geoportal'].each { service ->
                                        def end_line = sh(returnStdout: true, script: "(cd ${HOME}/workspace/testgeomapfish/; docker-compose logs ${service}) | wc -l") as Integer
                                        sh "(cd ${HOME}/workspace/testgeomapfish/; docker-compose logs --timestamps --tail=${Math.max(1, end_line - start_lines.service)} ${service})"
                                    }
                                    throw error
                                }
                            }
                        } catch (Exception error) {
                            sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose logs --timestamps)'
                            throw error
                        } finally {
                            sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose down)'
                        }
                    }
                    sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-run travis/short-make --makefile=travis.mk build)'
                    sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-run make --makefile=travis.mk checks)'
                    sh '''find \
                        ${HOME}/workspace/testgeomapfish/geoportal/setup.py \
                        ${HOME}/workspace/testgeomapfish/geoportal/testgeomapfish_geoportal/*.py \
                        ${HOME}/workspace/testgeomapfish/geoportal/testgeomapfish_geoportal/views \
                        ${HOME}/workspace/testgeomapfish/commons/setup.py \
                        ${HOME}/workspace/testgeomapfish/commons/testgeomapfish_commons \
                        -name \\*.py | xargs travis/squote'''
                    sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-run travis/status.sh)'
                    sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-run make --makefile=empty-vars.mk geoportal/config.yaml)'
                    sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-run make --makefile=travis.mk alembic.ini)'
                    try {
                        sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-compose-run alembic --name=main upgrade head)'
                        sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-compose-run alembic --name=static upgrade head)'
                        sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-compose-run alembic --name=static downgrade base)'
                        sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-compose-run alembic --name=main downgrade base)'
                    } catch (Exception error) {
                        sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose --file=docker-compose-build.yaml logs)'
                        throw error
                    } finally {
                        sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose --file=docker-compose-build.yaml down)'
                    }
                    sh 'rm -rf ${HOME}/workspace/testgeomapfish'
                }, 'Tests upgrades': {
                    try {
                        sh 'docker run --name geomapfish-db --env=POSTGRES_USER=www-data --env=POSTGRES_PASSWORD=www-data --env=POSTGRES_DB=geomapfish --publish=5432:5432 --detach camptocamp/geomapfish-test-db'
                        sh 'travis/test-upgrade-convert.sh init ${HOME}/workspace'
                        // Test Upgrade an convert project
                        sh 'travis/test-upgrade-convert.sh v220-todocker ${HOME}/workspace'
                        sh 'travis/test-upgrade-convert.sh v220-tonondocker ${HOME}/workspace'
                        sh 'travis/test-upgrade-convert.sh docker ${HOME}/workspace'
                        sh 'travis/test-upgrade-convert.sh tonondocker ${HOME}/workspace'
                        sh 'travis/test-upgrade-convert.sh nondocker ${HOME}/workspace'
                        sh 'travis/test-upgrade-convert.sh todocker ${HOME}/workspace'
                    } finally {
                        sh 'docker stop geomapfish-db'
                        sh 'docker rm --volumes geomapfish-db'
                    }
                }
            }
        } finally {
            stage('Clean') {
                clean()
            }
        }
    }
}
