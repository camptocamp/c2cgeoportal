#!groovy
@Library('c2c-pipeline-library')
import static com.camptocamp.utils.*

final MAIN_BRANCH = '2.4'
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
    sh 'docker network rm internal || true'

    sh 'docker ps'
    sh 'docker ps --all --filter status=exited'
    sh 'docker volume ls'

    sh 'travis/test-upgrade-convert.sh cleanup ${HOME}/workspace'
    sh 'rm -rf ${HOME}/workspace/testgeomapfishapp'
    sh 'rm -rf ${HOME}/workspace/geomapfish'
}

def get_abort_ci() {
    // Makes sure Jenkins will not build his own commit
    COMMITTER = sh(returnStdout: true, script: "git show --no-patch --format='%ae' HEAD").trim()
    TAG = sh(returnStdout: true, script: 'git tag --list --points-at=HEAD').trim()
    USER_START = currentBuild.getBuildCauses()[0].get('shortDescription').startsWith('Started by user ')
    if (COMMITTER == 'ci@camptocamp.com' && TAG == "" && !USER_START) {
        return true
    }
    return false
}

def test_upgrade(String task, String src, String ref) {
    try {
        sh "travis/test-upgrade-convert.sh ${task} ${HOME}/workspace"
    } catch (Exception error) {
        sh "(cd ${HOME}/workspace/${src}/testgeomapfish; ./docker-run make clean-all) || true"
        sh "(cd ${HOME}/workspace/${src}/testgeomapfish; rm --recursive --force .UPGRADE* \
            commons/testgeomapfish_commons.egg-info geoportal/testgeomapfish_geoportal.egg-info) || true"
        sh "find ${HOME}/workspace/${src} -type d -empty -delete || true"
        sh "diff --recursive --exclude=.git --exclude=locale ${HOME}/workspace/${ref} ${HOME}/workspace/${src}"
        throw error
    }
}

should_abort_ci = false

def abort_ci() {
    if (should_abort_ci) {
        // Return here instead of throwing error to keep the build "green"
        currentBuild.result = 'SUCCESS'
    }
    return should_abort_ci
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
                sh 'git config user.email ci@camptocamp.com'
                sh 'git config user.name CI'
                sh 'git branch --delete --force ${BRANCH_NAME} || true'
                sh 'git checkout -b ${BRANCH_NAME}'
                sh 'git remote set-url origin git@github.com:camptocamp/c2cgeoportal.git'
                sshagent (credentials: ['c2c-infra-ci']) {
                    sh 'git fetch --tags'
                }

                should_abort_ci = get_abort_ci()
                if (abort_ci()) { return }

                sh 'python3 -m venv .venv'
                sh '.venv/bin/python .venv/bin/pip install --requirement=travis/requirements.txt'

                TAG = sh(returnStdout: true, script: 'git tag --list --points-at=HEAD').trim()
                LAST_TAG = sh(returnStdout: true, script: 'git describe --abbrev=0 --tags').trim()
                RELEASE_TAG = MAJOR_VERSION
                if (TAG =~ /^[0-9]+\.[0-9]+\.[0-9]+$/) {
                    println("Release detected")
                    RELEASE_TAG = TAG
                }
                else if (TAG =~ /^[0-9]+\.[0-9]+\.[0-9]+\.dev[0-9]+$/) {
                    println("Dev release detected")
                    RELEASE_TAG = TAG
                }
                else if (TAG =~ /^[0-9]+\.[0-9]+\.[0-9]+\.?rc[0-9]+$/) {
                    println("RC release detected")
                    RELEASE_TAG = TAG
                }
                else {
                    if (BRANCH_NAME =~ /^[0-9]\.[0-9]$/) {
                        println("Release branch detected")
                        MINOR = sh(returnStdout: true, script: '.venv/bin/python travis/get-minor --no-save').trim()
                        RELEASE_TAG = "${LAST_TAG}.${MINOR}"
                    }
                }
                env.RELEASE_TAG = RELEASE_TAG

                sh 'make docker-pull'
                sh 'docker images'
                sh 'make docker-build'
                sh 'docker run --name geomapfish-db --env=POSTGRES_USER=www-data --env=POSTGRES_PASSWORD=www-data --env=POSTGRES_DB=geomapfish --publish=5432:5432 --detach camptocamp/geomapfish-test-db'
                sh './docker-run travis/status.sh'
                sh './docker-run --env=RELEASE_TAG travis/short-make build'
                sh "docker tag camptocamp/geomapfish-build:${MAJOR_VERSION} camptocamp/geomapfish-build:${RELEASE_TAG}"
                sh "docker tag camptocamp/geomapfish-config-build:${MAJOR_VERSION} camptocamp/geomapfish-config-build:${RELEASE_TAG}"
                sh 'travis/test-upgrade-convert.sh init ${HOME}/workspace'
            }
            stage('Tests') {
                if (abort_ci()) { return }
                parallel 'Lint c2cgeoportal': {
                    // lint
                    sh './docker-run make checks'
                    sh './docker-run travis/empty-make help'
                    sh 'bash -c "test \\"`./docker-run id`\\" == \\"uid=0(root) gid=0(root) groups=0(root)\\""'
                    sh './docker-run make doc'
                    // Test return code
                    sh './docker-run true'
                    sh 'if ./docker-run false; then false; fi'
                    lock("docker-compose-run-${env.NODE_NAME}") {
                        try {
                            sh './docker-compose-run true'
                            sh 'if ./docker-compose-run false; then false; fi'
                        } catch (Exception error) {
                            sh 'docker-compose logs --timestamps'
                            throw error
                        } finally {
                            sh 'docker-compose down'
                        }
                    }
                }, 'Test c2cgeoportal': {
                    sh './docker-run make prepare-tests'
                    sh './docker-run travis/status.sh'
                    lock("docker-compose-run-${env.NODE_NAME}") {
                        try {
                            sh './docker-compose-run alembic --config=geoportal/tests/functional/alembic.ini --name=main upgrade head'
                            sh './docker-compose-run alembic --config=geoportal/tests/functional/alembic.ini --name=static upgrade head'
                            timeout(time: 10, unit: 'MINUTES') {
                                sh './docker-compose-run make tests'
                            }
                        } catch (Exception error) {
                            sh 'docker-compose logs --timestamps'
                            throw error
                        } finally {
                            sh 'docker-compose down'
                        }
                    }
                    sh './docker-run travis/codacy.sh'
                    sh './docker-run travis/status.sh'
                }, 'Test QGIS server plugin': {
                    sh 'cd docker/qgisserver; make build-tests'
                    try {
                        sh 'cd docker/qgisserver/tests; docker-compose run --rm qgisserver-tests'
                    } catch (Exception error) {
                        sh 'cd docker/qgisserver/tests; docker-compose logs --timestamps'
                        throw error
                    } finally {
                        sh 'cd docker/qgisserver/tests; docker-compose down'
                    }
                }, 'Test Docker app': {
                    // Use an internal network to be sure that we have everything we needs in the Docker images
                    sh 'docker network create --internal internal'
                    sh './docker-run make docker-build-test'
                    sh 'docker run --detach --network=internal --name=test-db --network-alias=db camptocamp/geomapfish-test-db:latest'
                    sh 'docker run --detach --network=internal --name=test-externaldb --network-alias=externaldb camptocamp/geomapfish-test-external-db:latest'
                    env.PGHOST='db'
                    env.PGHOST_SLAVE='db'

                    sh 'rm -rf ${HOME}/workspace/testgeomapfishapp'

                    lock("docker-compose-run-${env.NODE_NAME}") {
                        try {
                            sh 'travis/create-new-project.sh ${HOME}/workspace'
                            sh '(cd ${HOME}/workspace/testgeomapfishapp/; ./docker-compose-run make --makefile=travis.mk update-po)'
                        } catch (Exception error) {
                            sh '(cd ${HOME}/workspace/testgeomapfishapp/; docker-compose --file=docker-compose-build.yaml logs --timestamps)'
                            throw error
                        } finally {
                            // down will lost the default theme
                            sh '(cd ${HOME}/workspace/testgeomapfishapp/; docker-compose --file=docker-compose-build.yaml stop)'
                        }
                    }
                    // Commit the l10n files modifications
                    // To prevent fail on modification files check
                    sh '(cd ${HOME}/workspace/testgeomapfishapp/; git add geoportal/testgeomapfishapp_geoportal/locale/*/LC_MESSAGES/testgeomapfishapp_geoportal-*.po)'
                    sh '(cd ${HOME}/workspace/testgeomapfishapp/; git commit -m "Upgrade the po files")'
                    sh '(cd ${HOME}/workspace/testgeomapfishapp/; ./docker-run travis/empty-make --makefile=travis.mk help)'
                    sh '(cd ${HOME}/workspace/testgeomapfishapp/; ./docker-run make --makefile=travis.mk build)'
                    withCredentials([[
                        $class: 'UsernamePasswordMultiBinding',
                        credentialsId: 'dockerhub',
                        usernameVariable: 'USERNAME',
                        passwordVariable: 'PASSWORD'
                    ]]) {
                        lock("docker-compose-run-${env.NODE_NAME}") {
                            try {
                                sh 'docker login -u "$USERNAME" -p "$PASSWORD"'
                                sh 'cat ${HOME}/workspace/testgeomapfishapp/docker-compose.yaml'
                                sh '(cd ${HOME}/workspace/testgeomapfishapp/; docker-compose up -d)'
                                timeout(time: 2, unit: 'MINUTES') {
                                    sh '(cd ${HOME}/workspace/testgeomapfishapp/; docker-compose exec -T geoportal wait-db)'
                                    sh '(cd ${HOME}/workspace/testgeomapfishapp/; docker-compose exec -T geoportal bash -c "PGHOST=externaldb PGDATABASE=test wait-db;")'
                                    sh '(cd ${HOME}/workspace/testgeomapfishapp/; docker-compose exec -T geoportal create-demo-theme)'
                                    sh '(cd ${HOME}/workspace/testgeomapfishapp/; docker-compose exec -T geoportal theme2fts)'
                                    sh './docker-run --network=internal travis/waitwsgi http://front/'
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
                                    ['print', 'mapserver', 'geoportal'].each { service ->
                                        def start_line = sh(returnStdout: true, script: "(cd ${HOME}/workspace/testgeomapfishapp/; docker-compose logs ${service}) | wc -l") as Integer
                                        start_lines.service = start_line
                                    }
                                    try {
                                        // See also:
                                        // travis/vars.yaml geoportal/GUNICORN_PARAMS
                                        // test-new-project timeout
                                        timeout(3) {
                                            sh "./docker-run --network=internal travis/test-new-project http://front/${path}"
                                        }
                                    } catch (Exception error) {
                                        sh './docker-run --network=internal curl http://front/c2c/debug/stacks?secret=c2c'
                                        ['print', 'mapserver', 'geoportal'].each { service ->
                                            def end_line = sh(returnStdout: true, script: "(cd ${HOME}/workspace/testgeomapfishapp/; docker-compose logs ${service}) | wc -l") as Integer
                                            sh "(cd ${HOME}/workspace/testgeomapfishapp/; docker-compose logs --timestamps --tail=${Math.max(1, end_line - start_lines.service)} ${service})"
                                        }
                                        throw error
                                    }
                                }
                            } catch (Exception error) {
                                sh '(cd ${HOME}/workspace/testgeomapfishapp/; docker-compose logs --timestamps)'
                                sh 'docker logs test-db'
                                sh 'docker logs test-externaldb'
                                throw error
                            } finally {
                                sh '(cd ${HOME}/workspace/testgeomapfishapp/; docker-compose down)'
                            }
                        }
                    }
                    sh '(cd ${HOME}/workspace/testgeomapfishapp/; ./docker-run travis/short-make --makefile=travis.mk build)'
                    sh '(cd ${HOME}/workspace/testgeomapfishapp/; ./docker-run make --makefile=travis.mk checks)'
                    sh '''find \
                        ${HOME}/workspace/testgeomapfishapp/geoportal/setup.py \
                        ${HOME}/workspace/testgeomapfishapp/geoportal/testgeomapfishapp_geoportal/*.py \
                        ${HOME}/workspace/testgeomapfishapp/geoportal/testgeomapfishapp_geoportal/views \
                        ${HOME}/workspace/testgeomapfishapp/commons/setup.py \
                        ${HOME}/workspace/testgeomapfishapp/commons/testgeomapfishapp_commons \
                        -name \\*.py | xargs travis/squote'''
                    sh '(cd ${HOME}/workspace/testgeomapfishapp/; ./docker-run travis/status.sh)'
                    sh '(cd ${HOME}/workspace/testgeomapfishapp/; ./docker-run make --makefile=empty-vars.mk geoportal/config.yaml)'
                    sh '(cd ${HOME}/workspace/testgeomapfishapp/; ./docker-run make --makefile=travis.mk geoportal/alembic.ini)'
                    lock("docker-compose-run-${env.NODE_NAME}") {
                        try {
                            sh '(cd ${HOME}/workspace/testgeomapfishapp/; ./docker-compose-run alembic --config=geoportal/alembic.ini --name=main upgrade head)'
                            sh '(cd ${HOME}/workspace/testgeomapfishapp/; ./docker-compose-run alembic --config=geoportal/alembic.ini --name=static upgrade head)'
                            sh '(cd ${HOME}/workspace/testgeomapfishapp/; ./docker-compose-run alembic --config=geoportal/alembic.ini --name=static downgrade base)'
                            sh '(cd ${HOME}/workspace/testgeomapfishapp/; ./docker-compose-run alembic --config=geoportal/alembic.ini --name=main downgrade base)'
                        } catch (Exception error) {
                            sh '(cd ${HOME}/workspace/testgeomapfishapp/; docker-compose --file=docker-compose-build.yaml logs --timestamps)'
                            throw error
                        } finally {
                            sh '(cd ${HOME}/workspace/testgeomapfishapp/; docker-compose --file=docker-compose-build.yaml down)'
                        }
                    }
                    sh 'rm -rf ${HOME}/workspace/testgeomapfishapp'
                }, 'Tests upgrades 220': {
                    sh 'travis/test-upgrade-convert.sh init ${HOME}/workspace'
                    // Test Upgrade an convert project
                    test_upgrade('v220-todocker', 'v220-todocker', 'dockerref')
                    test_upgrade('v220-tonondocker', 'v220-tonondocker', 'nondockerref')
                }
            }

            stage('Test Upgrade') {
                if (abort_ci()) { return }
                parallel 'Tests upgrades Docker': {
                    test_upgrade('docker', 'docker', 'dockerref')
                }, 'Tests upgrades non Docker': {
                    test_upgrade('nondocker', 'nondocker', 'nondockerref')
                    test_upgrade('todocker', 'nondocker', 'dockerref')
                }, 'Tests upgrades 230': {
                    test_upgrade('v230-docker', 'v230-docker', 'dockerref')
                    test_upgrade('v230-nondocker', 'v230-nondocker', 'nondockerref')
                }, 'Tests upgrades 240': {
                    test_upgrade('v240', 'v240', 'dockerref')
                }
            }
            stage('Publish') {
                if (abort_ci()) { return }
                parallel 'Push to Docker hub and Pypi': {
                    sh 'git remote add full https://github.com/camptocamp/c2cgeoportal.git || true'
                    sh 'git remote set-url full https://github.com/camptocamp/c2cgeoportal.git'
                    sh 'git fetch --tags --prune full'

                    sh "travis/create-new-project.sh ${HOME}/workspace geomapfish"
                    withCredentials([
                        string(credentialsId: 'docker-hub', variable: 'DOCKER_PASSWORD'),
                        [
                             $class: 'UsernamePasswordMultiBinding',
                             credentialsId: 'pypi_sbrunner',
                             usernameVariable: 'PYPI_USERNAME',
                             passwordVariable: 'PYPI_PASSWORD',
                        ]
                    ]) {
                        env.DOCKER_PASSWORD = DOCKER_PASSWORD
                        env.PYPI_USERNAME = PYPI_USERNAME
                        env.PYPI_PASSWORD = PYPI_PASSWORD

                        sh '.venv/bin/python travis/clean-dockerhub-tags'

                        sshagent (credentials: ['c2c-infra-ci']) {
                            sh 'travis/publish'
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
                if (abort_ci()) { return }
                sh './docker-run make doc'
                sshagent (credentials: ['c2c-infra-ci']) {
                    sh 'travis/doc.sh'
                }
            }
        } finally {
            stage('Clean') {
                if (abort_ci()) { return }
                sh 'docker stop geomapfish-db'
                sh 'docker rm --volumes geomapfish-db'
                clean()
            }
        }
    }
}
