node('python-build-slave') {
def credentials
def aws_region
def datadog_key
    properties([
            [$class: 'ParametersDefinitionProperty', parameterDefinitions: [
                    [
                            $class     : 'ChoiceParameterDefinition',
                            choices    : 'NO DEPLOY\ndev-us\nstg-us\nprod\n',
                            description: 'What environment to deploy to?',
                            name       : 'ENV'
                    ], [
                            $class     : 'StringParameterDefinition',
                            description: 'What git tag/branch to deploy from?',
                            name       : 'DEPLOY_TAG',
                            defaultValue: 'master'
                    ]
            ]],
            [$class: 'BuildDiscarderProperty', strategy: [
                    $class: 'LogRotator',
                    numToKeepStr: '20'
            ]]
    ])

    echo "ENV: ${params.ENV}"

    stage('Preparation') {
        checkout([
            $class: 'GitSCM',
            branches: scm.branches,
            extensions: scm.extensions + [
                [$class: 'LocalBranch', localBranch: params.DEPLOY_TAG],
                [$class: 'WipeWorkspace']
            ],
            userRemoteConfigs: scm.userRemoteConfigs
        ])

        //checkout cloudformation-templates repo where we have all utility scripts
         sh 'mkdir -p cloudformation-templates'
         dir("cloudformation-templates"){
            checkout([
                $class: 'GitSCM',
                branches: [[name: '*/master']],
                browser: [$class: 'GitWeb'],
                doGenerateSubmoduleConfigurations: false,
                extensions: [], submoduleCfg: [],
                userRemoteConfigs: [[credentialsId: 'facaebc2-6604-4230-bb66-5e6976561adf', url: 'git@github.com:tendrilinc/cloudformation-templates.git']]])
         }
        //update AWS credentials and region info
        if (params.ENV ==~ /(dev-us|stg-us|prod)/) {
            credentials = get_credentials(params.ENV)
            aws_region = get_aws_region(params.ENV)
        }
    }

    stage('Tests') {
        try {
            sh './run_tests.sh'
        } finally {
            if (fileExists('nosetests.xml'))
                junit 'nosetests.xml'
        }
    }



    // I really really wanted to separate the deploy stages into 3 separate directives (one for each environment)
    // so that they'll all appear in the Jenkins UI, but there isn't a way to "ignore" stages that don't do
    // anything (ie does not satisfy the if condition).  It still shows green, as executed, which can be very
    // mis-leading.
    // EXAMPLE
    //    stage('Deploy To dev-us') {
    //        if (params.ENV == 'dev-us') {
    //            deploy(params.ENV)
    //        }
    //    }
    // The alternative was to dynamically create the stage name, but the Jenkins UI again acts weird when you
    // switch the stage name from '...dev-us' to '...stg-us', it blows away the pipeline build history :(
    if (params.ENV ==~ /(dev-us|stg-us|prod)/) {
        stage('Deploy') {
            create_infra_stack(params.ENV,credentials,aws_region)
            create_update_stack(params.ENV,credentials,aws_region)
        }
    }

    if (params.ENV ==~ /(dev-us|stg-us|prod)/) {
        stage('Update Log Subscription') {
            funcNames = get_lambda_functions(params.ENV,credentials,aws_region)
            custom_name = get_custom_name()

            datadog_key = get_datadog_key(params.ENV,credentials,aws_region)
            create_log_groups(params.ENV,credentials,aws_region,funcNames,custom_name)
            create_log_forwarding_stack(params.ENV,credentials,aws_region,custom_name,datadog_key)

            update_subscriptions(params.ENV,credentials,aws_region,funcNames,custom_name)
        }
    }
}

def get_credentials(String env) {
    def credential_values
    if (env == 'prod') {
        credential_values = [
                [
                        $class           : 'AmazonWebServicesCredentialsBinding',
                        credentialsId    : '4b25eff4-7dba-42f5-8304-b81b00995a93',
                        accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                        secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                ]
        ]
    } else if (env == 'stg-us') {
        credential_values = [
                [
                        $class           : 'AmazonWebServicesCredentialsBinding',
                        credentialsId    : 'aws-jenkins-stg-us',
                        accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                        secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                ]
        ]
    } else {
        credential_values = [
                [
                        $class           : 'AmazonWebServicesCredentialsBinding',
                        credentialsId    : 'aws-jenkins-dev',
                        accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                        secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                ]
        ]
    }

    return credential_values
}

def get_aws_region(String env){
    def aws_region = 'us-east-1'
    if (env == 'stg-us') {
        aws_region = 'us-west-2'
    }
    return aws_region
}


def get_datadog_key(String env,credentials,aws_region) {
    withCredentials(credentials) {
        withEnv(['LC_ALL=C.UTF-8', 'LANG=C.UTF-8', "AWS_DEFAULT_REGION=${aws_region}"]) {
            return sh (returnStdout: true, script: """
            aws secretsmanager get-secret-value --secret-id datadog --query SecretString --output text  | python3 -c "import sys, json; print(json.load(sys.stdin)['API_KEY'])"
            """).trim()
        }
    }
}



def create_infra_stack(String env,credentials,aws_region) {
    withCredentials(credentials) {
        withEnv(['LC_ALL=C.UTF-8', 'LANG=C.UTF-8', "AWS_DEFAULT_REGION=${aws_region}"]) {
            sh ("""
            stack_name=chalice-template-${env}
            infra_stack_name=chalice-template-infrastructure-${env}

            if [ \$(aws cloudformation describe-stacks | grep StackName | grep \${infra_stack_name} | wc -l) -eq 0 ]
                then
                 aws cloudformation create-stack --stack-name=\${infra_stack_name} --template-body file://config/cloudformation.yml --parameters ParameterKey=Environment,ParameterValue=${env}
                 echo "Waiting for stack creation to complete"
                 aws cloudformation wait stack-create-complete --region $aws_region --stack-name \$infra_stack_name
                 echo "Stack creation complete"
            else
                echo "\${infra_stack_name} already exist"
            fi
                """)
        }
    }
}

def create_update_stack(String env,credentials,aws_region) {
    withCredentials(credentials) {
        withEnv(['LC_ALL=C.UTF-8', 'LANG=C.UTF-8', "AWS_DEFAULT_REGION=${aws_region}"]) {
            sh "chalice package build/ --stage ${env}"
            sh "aws cloudformation package --template-file build/sam.json --s3-bucket chalice-template-build-artifacts-${env} --output-template-file build/packaged.yml"
            sh "aws cloudformation deploy --template-file build/packaged.yml --stack-name chalice-template-${env} --capabilities CAPABILITY_IAM"
        }
    }
}




def get_lambda_functions(String env,credentials,aws_region) {
    withCredentials(credentials) {
        withEnv(['LC_ALL=C.UTF-8', 'LANG=C.UTF-8', "AWS_DEFAULT_REGION=${aws_region}"]) {
            println "fetching all lambda functions..."
            functions = sh (returnStdout: true, script:
            """
            pyenv local 3.6.2
            stack_name=chalice-template-${env}

            physicalResources=\$(aws cloudformation describe-stack-resources --stack-name=\${stack_name} --query 'StackResources[?ResourceType==`AWS::Lambda::Function`].PhysicalResourceId' --output text)
            echo \${physicalResources}
            """).trim()
            println functions
            return functions.tokenize()
        }
    }
}

def get_custom_name(){
    println "getting custom_name.."
	custom_name = sh (returnStdout: true, script: "echo chalice-template").trim()
	if(custom_name.length() >= 40) {
		custom_name = custom_name.substring(0,40)
	}
	println "custom_name is $custom_name"
    return custom_name
}


def create_log_forwarding_stack(String env,credentials,aws_region,custom_name,datadog_key){
    withCredentials(credentials) {
        withEnv(['LC_ALL=C.UTF-8', 'LANG=C.UTF-8', "AWS_DEFAULT_REGION=${aws_region}"]) {
            println "creating log forwarding lambda.."
            sh (
            """
            pyenv local 3.6.2
            if [ \$(aws cloudformation describe-stacks | grep StackName | grep  lambda-for-${custom_name}-log-streaming | wc -l) -eq 0 ]
                then
                    cd cloudformation-templates/log-streaming/
                    echo "creating service-specific-lambda "
                    ./create-service-specific-lambda.sh --env $env --region ${aws_region} --service ${custom_name} --datadogkey ${datadog_key}
            else
                echo "lambda-for-${custom_name}-log-streaming stack already exists"
            fi
            """)
        }
    }
}


def create_log_groups(env,credentials,aws_region,funcNames,custom_name){
    println "creating log groups.."
    for(funName in funcNames) {
      log_group_name = "/aws/lambda/"+funName
      create_log_group(log_group_name,env,credentials,aws_region)
    }
}

def update_subscriptions(env,credentials,aws_region,funcNames,custom_name){
    println "updating subscriptions.."
    for(funName in funcNames) {
      log_group_name = "/aws/lambda/"+funName
      update_subscription(env,credentials,aws_region,log_group_name,custom_name)
    }
}

def create_log_group(log_group_name,env,credentials,aws_region){
  withCredentials(credentials){
    withEnv(['LC_ALL=C.UTF-8', 'LANG=C.UTF-8', "AWS_DEFAULT_REGION=${aws_region}"]){
      sh ("""
      pyenv local 3.6.2
      if [ \$(aws logs describe-log-groups --log-group-name-prefix=${log_group_name} --query logGroups[].logGroupName | grep ${log_group_name} | wc -l) -eq 0 ]
        then
        aws logs create-log-group --log-group-name ${log_group_name} && echo "${log_group_name}" || echo "ERROR: Unable to create log group"
      else
        echo "${log_group_name} log group already exist"
      fi

      """)
      }
    }
  }


def update_subscription(String env,credentials,aws_region,log_group_name,custom_name) {
    withCredentials(credentials) {
        withEnv(['LC_ALL=C.UTF-8', 'LANG=C.UTF-8', "AWS_DEFAULT_REGION=${aws_region}"]) {
            println "updating subscription..."
            sh ("""
            cd cloudformation-templates/log-streaming/
            ls -l
            echo "Update log-group ${log_group_name} subscription"
            ./update-subscription-filter.sh --log-group ${log_group_name} --region ${aws_region} --function-name ${custom_name}-logs-to-datadog-${env}
            """)
        }
    }
}

