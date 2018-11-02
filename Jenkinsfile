#!groovy
@Library('c2c-pipeline-library')
import static com.camptocamp.utils.*

final MAIN_BRANCH = 'master'
env.MAIN_BRANCH = MAIN_BRANCH
final MAJOR_VERSION = '2.4'
env.MAJOR_VERSION = MAJOR_VERSION
env.CI = 'true'
env.DOCKER_USERNAME = 'amplerancid'

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
    sh 'rm -rf ${HOME}/workspace/geomapfish'
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

                // Makes sure jenkins will not build his own commit
                if (sh(returnStdout: true, script: "git show --no-patch --format='%ae' HEAD") == 'ci@camptocamp.com') {
                    exit(0)
                }
                sh 'git config user.email ci@camptocamp.com'
                sh 'git config user.name CI'
                try {
                    sh 'git branch --delete --force ${BRANCH_NAME}'
                } catch (Exception error) {}
                sh 'git checkout -b ${BRANCH_NAME}'
                sh 'git remote set-url origin git@github.com:camptocamp/c2cgeoportal.git'

                sh 'python3 -m venv .venv'
                sh '.venv/bin/python .venv/bin/pip install --requirement=travis/requirements.txt'

                sh 'make docker-build'
                sh 'docker run --name geomapfish-db --env=POSTGRES_USER=www-data --env=POSTGRES_PASSWORD=www-data --env=POSTGRES_DB=geomapfish --publish=5432:5432 --detach camptocamp/geomapfish-test-db'
                sh './docker-run travis/status.sh'
                sh './docker-run travis/short-make build'
            }
            stage('Tests') {
                checkout scm
                parallel 'Lint and test c2cgeoportal': {
                    sh './docker-run travis/empty-make help'
                    sh 'bash -c "test \\"`./docker-run id`\\" == \\"uid=0(root) gid=0(root) groups=0(root)\\""'
                    sh './docker-run make doc'
                    // lint
                    sh './docker-run make checks'
                    // Test return code
                    sh './docker-run true'
                    sh 'if ./docker-run false; then false; fi'
                    try {
                        sh './docker-compose-run true'
                        sh 'if ./docker-compose-run false; then false; fi'
                    } catch (Exception error) {
                        sh 'docker-compose logs --timestamps'
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
                        sh 'docker-compose logs --timestamps'
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
                        sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-compose-run make --makefile=travis.mk update-po)'
                    } catch (Exception error) {
                        sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose --file=docker-compose-build.yaml logs --timestamps)'
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
                    withCredentials([[
                        $class: 'UsernamePasswordMultiBinding',
                        credentialsId: 'dockerhub',
                        usernameVariable: 'USERNAME',
                        passwordVariable: 'PASSWORD'
                    ]]) {
                        try {
                            sh 'docker login -u "$USERNAME" -p "$PASSWORD"'
                            sh 'cat ${HOME}/workspace/testgeomapfish/docker-compose.yaml'
                            sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose up -d)'
                            timeout(time: 2, unit: 'MINUTES') {
                                sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose exec -T geoportal wait-db)'
                                sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose exec -T geoportal bash -c "PGHOST=externaldb PGDATABASE=test wait-db;")'
                                sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose exec -T geoportal create-demo-theme)'
                                sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose exec -T geoportal theme2fts)'
                                sh './docker-run --network=testgeomapfishmain_internal travis/waitwsgi http://front/'
                            }
                            for (path in [
                                'c2c/health_check',
                                'c2c/health_check?max_level=9',
                                'c2c/health_check?checks=check_collector',
                                'layers/test/values/type enum',
                                'admin/layertree',
                                'admin/layertree/children'
                            ]) {
                                def start_lines = [:]
                                ['db', 'externaldb', 'print', 'mapserver', 'geoportal'].each { service ->
                                    def start_line = sh(returnStdout: true, script: "(cd ${HOME}/workspace/testgeomapfish/; docker-compose logs ${service}) | wc -l") as Integer
                                    start_lines.service = start_line
                                }
                                try {
                                    // See also:
                                    // travis/vars.yaml geoportal/GUNICORN_PARAMS
                                    // test-new-project timeout
                                    timeout(3) {
                                        sh './docker-run --network=testgeomapfishmain_internal travis/test-new-project http://front/${path}'
                                    }
                                } catch (Exception error) {
                                    sh './docker-run --network=testgeomapfishmain_internal curl http://front/c2c/debug/stacks?secret=c2c'
                                    ['db', 'externaldb', 'print', 'mapserver', 'geoportal'].each { service ->
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
                    sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-run make --makefile=travis.mk geoportal/alembic.ini)'
                    try {
                        sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-compose-run alembic --config=geoportal/alembic.ini --name=main upgrade head)'
                        sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-compose-run alembic --config=geoportal/alembic.ini --name=static upgrade head)'
                        sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-compose-run alembic --config=geoportal/alembic.ini --name=static downgrade base)'
                        sh '(cd ${HOME}/workspace/testgeomapfish/; ./docker-compose-run alembic --config=geoportal/alembic.ini --name=main downgrade base)'
                    } catch (Exception error) {
                        sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose --file=docker-compose-build.yaml logs --timestamps)'
                        throw error
                    } finally {
                        sh '(cd ${HOME}/workspace/testgeomapfish/; docker-compose --file=docker-compose-build.yaml down)'
                    }
                    sh 'rm -rf ${HOME}/workspace/testgeomapfish'
                }, 'Tests upgrades 220': {
                    sh 'travis/test-upgrade-convert.sh init ${HOME}/workspace'
                    // Test Upgrade an convert project
                    sh 'travis/test-upgrade-convert.sh v220-todocker ${HOME}/workspace'
                    sh 'travis/test-upgrade-convert.sh v220-tonondocker ${HOME}/workspace'
                }
            }
            stage('Test Upgrade') {
                parallel 'Tests upgrades Docker': {
                    sh 'travis/test-upgrade-convert.sh docker ${HOME}/workspace'
                    sh 'travis/test-upgrade-convert.sh tonondocker ${HOME}/workspace'
                }, 'Tests upgrades non Docker': {
                    sh 'travis/test-upgrade-convert.sh nondocker ${HOME}/workspace'
                    sh 'travis/test-upgrade-convert.sh todocker ${HOME}/workspace'
                }, 'Tests upgrades 230': {
                    sh 'travis/test-upgrade-convert.sh v230-docker ${HOME}/workspace'
                    sh 'travis/test-upgrade-convert.sh v230-nondocker ${HOME}/workspace'
                }
            }
            stage('Publish') {
                parallel 'Push to Docker hub': {
                    sh 'git remote add full https://github.com/camptocamp/c2cgeoportal.git || true'
                    sh 'git remote set-url full https://github.com/camptocamp/c2cgeoportal.git'
                    sh 'git fetch --tags --prune full'

                    sh "travis/create-new-project.sh ${HOME}/workspace geomapfish"
                    withCredentials([string(credentialsId: 'docker-hub', variable: 'DOCKER_PASSWORD')]) {
                        env.DOCKER_PASSWORD = DOCKER_PASSWORD

                        sh '.venv/bin/python travis/clean-dockerhub-tags'

                        sshagent (credentials: ['c2c-infra-ci']) {
                            sh 'travis/publish-docker'
                        }
                    }
                }, 'Push to Transifex': {
                    branch = sh(returnStdout: true, script: 'git rev-parse --abbrev-ref HEAD')
                    if (branch == MAIN_BRANCH) {
                        withCredentials([string(credentialsId: 'transifex-sbrunner', variable: 'TRANSIFEX_PASSWORD')]) {
                            sh 'echo "[https://www.transifex.com]" > ~/.transifexrc'
                            sh 'echo "hostname = https://www.transifex.com" >> ~/.transifexrc'
                            sh 'echo "username = stephane.brunner@camptocamp.com" >> ~/.transifexrc'
                            sh "echo 'password = ${TRANSIFEX_PASSWORD}' >> ~/.transifexrc"
                            sh 'echo "token =" >> ~/.transifexrc'
                            sh './docker-run --home make transifex-send'
                        }
                    }
                }
            }
            stage('Publish documentation to GitHub.io') {
                sh './docker-run make doc'
                sshagent (credentials: ['c2c-infra-ci']) {
                    sh 'travis/doc.sh'
                }
            }
        } finally {
            stage('Clean') {
                sh 'docker stop geomapfish-db'
                sh 'docker rm --volumes geomapfish-db'
                clean()
            }
        }
    }
}
