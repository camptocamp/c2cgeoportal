#!groovy
@Library('c2c-pipeline-library')
import static com.camptocamp.utils.*

final MAIN_BRANCH = '2.3'
env.MAIN_BRANCH = MAIN_BRANCH
final MAJOR_VERSION = '2.3'
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
                if (TAG =~ /^[0-9]\.[0-9]\.[0-9]$/) {
                    RELEASE_TAG = TAG
                }
                else {
                    if (BRANCH_NAME =~ /^[0-9]\.[0-9]$/) {
                        MINOR = sh(returnStdout: true, script: '.venv/bin/python travis/get-minor --no-save').trim()
                        RELEASE_TAG = "${LAST_TAG}.${MINOR}"
                    }
                }
                env.RELEASE_TAG = RELEASE_TAG

                sh 'make docker-build'
                sh "docker tag camptocamp/geomapfish-build:${MAJOR_VERSION} camptocamp/geomapfish-build:${RELEASE_TAG}"
            }
            stage('Publish') {
                if (abort_ci()) { return }
                parallel 'Push to Docker hub and Pypi': {
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
                sshagent (credentials: ['c2c-infra-ci']) {
                    sh 'travis/doc.sh'
                }
            }
        } finally {
            stage('Clean') {
                if (abort_ci()) { return }
                clean()
            }
        }
    }
}
