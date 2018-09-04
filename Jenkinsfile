#!groovy
@Library('c2c-pipeline-library@tests')
import static com.camptocamp.utils.*

final MAIN_BRANCH = 'master'
env.MAIN_BRANCH = MAIN_BRANCH
final MAJOR_VERSION_NUMBER = '2'
final MINOR_VERSION_NUMBER = '4'
env.MAJOR_VERSION = "${MAJOR_VERSION_NUMBER}.${MINOR_VERSION_NUMBER}"
env.CI = 'true'
String cron_string = BRANCH_NAME ==~  /release\/.*/ ? "@daily" : ""

@NonCPS
def getCauses(){
    return currentBuild.rawBuild.getCauses()
}

dockerBuild {
    pipelineTriggers(
        [
            [
                pollSCM(cron_string)
            ]
        ]
    )
    timeout(time: 2, unit: 'HOURS') {
        stage('Tag n release'){
            echo getCauses()

            if(getCauses()[0] instanceof hudson.triggers.TimerTrigger.TimerTriggerCause ){
                echo 'Timer cause'
            }
            if(getCauses()[0] instanceof  hudson.model.Cause.UserCause){
                echo 'user cause'
            }
            checkout scm

            if (env.BRANCH_NAME ==~ /release\/.*/){
                def old_version = readFile("${env.WORKSPACE}/version.txt").tokenize('.')
                echo "Tagging the new version : ${old_version[0]}.${old_version[1]}.${old_version[2].toInteger()+1}"
            }
        }
    }
}
