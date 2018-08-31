#!groovy
@Library('c2c-pipeline-library')
import static com.camptocamp.utils.*

final MAIN_BRANCH = 'master'
env.MAIN_BRANCH = MAIN_BRANCH
final MAJOR_VERSION_NUMBER = '2'
final MINOR_VERSION_NUMBER = '4'
env.MAJOR_VERSION = "${MAJOR_VERSION_NUMBER}.${MINOR_VERSION_NUMBER}"
env.CI = 'true'

dockerBuild {
    timeout(time: 2, unit: 'HOURS') {
        stage('Tag n release'){
            if (env.BRANCH_NAME ==~ /release\/.*/){
                echo "Tagging the new version : ${MAJOR_VERSION_NUMBER}.${MINOR_VERSION_NUMBER}.${BUILD_NUMBER}"
                git tag :"${MAJOR_VERSION_NUMBER}.${MINOR_VERSION_NUMBER}.${BUILD_NUMBER}"
            }
        }
    }
}
