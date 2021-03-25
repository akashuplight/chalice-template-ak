# chalice-template
_Provide a meaningful description of your project_

This project has been constructed using the `Chalice` microframework that handles the management, 
configuration and deployment of this serverless app.

[Dependencies](#dependencies)           
[Python Setup](#python-setup)            
[Infrastructure & Deployment](#infrastructure-and-deployment)      
[Development](#development)                
[Environment Variables](#environment-variables)                          
[RESTful](#restful)     

## Dependencies

* Python 3.6.2 
* [Chalice](https://chalice.readthedocs.io/en/latest/)
* AWS Lambda
* AWS Api Gateway
* AWS S3 (build artifacts only)

## Python Setup

It is highly recommended to leverage Python management tools to setup your development environment.
If that piques your interest, here are some steps you can take to do exactly that using `pyenv` (version management) 
and `pyenv-virtualenv` (environment management).

- if necessary: `brew install pyenv` and `brew install pyenv-virtualenv`
- enter the following lines in your preferred shell profile (ie. `.bash_profile`, `.zshrc`, etc)
  * `eval "$(pyenv init -)"`
  * `eval "$(pyenv virtualenv-init -)"`
- install a specific Python version: `pyenv install 3.6.2`
- create a new Python environment: `pyenv virtualenv 3.6.2 chalice-template`
- activate: `pyenv activate chalice-template`
- install dependencies: `pip install -r requirements.txt`
- install test dependencies: `pip install -r tests/requirements.txt`
- to deactivate: `pyenv deactivate`
- you might notice the `chalice` dependency lives in the `tests/requirements.txt`: this is intentional since it is not necessary to supply the main `requirements.txt`, but nice to have to run `chalice` locally.

## Infrastructure and Deployment 

#### Infrastructure
All the AWS dependencies for this service is managed by a CloudFormation (CF) template [file](config/cloudformation.yml).
In a vast majority of cases, this CF will have already been created.  Its intended to be ran only once, however, if updates 
are necessary here are examples of how to execute a CF create/update via `aws cli`.  

Be aware of `{env}`, you'll need to swap it out for the AWS environment your CF is applied against: dev-us, stg-us, or prod. 

If you followed [the wiki](https://wiki.tendrilinc.com/pages/viewpage.action?pageId=95715779), make sure the casing of your environment name in your ~/.aws/config file matches the casing in your `aws cli` command. Also, this cloudformation stack is distinct from the one that includes the lambda, it is just for infrastructure. 

*Validate*
```
aws cloudformation validate-template --template-body file://config/cloudformation.yml
```

*Create*
```
aws cloudformation create-stack --stack-name chalice-template-infrastructure-{env} --profile {env} --template-body file://config/cloudformation.yml --parameters ParameterKey=Environment,ParameterValue={env}
```

*Update*
```
aws cloudformation update-stack --stack-name chalice-template-infrastructure-{env} --profile {env} --template-body file://config/cloudformation.yml --parameters ParameterKey=Environment,ParameterValue={env}
```

*Describe*    
     
if your lambda is backed by an API Gateway, you can use this command to locate the EndpointURL (after a jenkins deploy)
```
aws cloudformation describe-stacks --stack-name chalice-template-{env} --profile dev-us
```

#### Deployment (CI/CD)
Jenkins handles all PR and Master builds/deployments via the [Jenkinsfile](Jenkinsfile).

*PR Builds/Deployments*

After a branch has been created, pushed to Github and a PR created, Jenkins will automatically create a PR build job 
[here](https://jenkins.useast.tni01.com:8443/job/Jenkinsfile%20Projects/job/chalice-template/).
If you'd like to deploy your changes from said branch, click into the PR instance an click `Build with Parameters`.
Then select the appropriate AWS environment (please refrain from pushing to PROD).

*Master Builds/Deployments*

Once a PR has been merged to master, the master jenkins job will automatically run.  When ready to deploy head
[here](https://jenkins.useast.tni01.com:8443/job/Jenkinsfile%20Projects/job/chalice-template/job/master/)
and select `Build with Parameters` and select the appropriate AWS environment.

Prior to a PRODUCTION deploy:
* Head to [Github](https://github.com/tendrilinc/chalice-template)
* Click the `releases` tab
* Click 'Create a new release' and complete the form given an appropriate `Tag version`
* Return back to Jenkins and deploy as normal

## Development

#### Chalice Requirements
Chalice is very particular in its directory structure while developing a service.  Here are some guidelines to follow
such that you won't run into any problems.

* All `@app.*` annotations (ie `@app.route()`) must be applied in the [app.py](%7B%7Bcookiecutter.project_slug%7D%7D/app.py) file
* Any and all custom python classes/scripts (.py), .json files, binary assets, etc must be placed under the `chalicelib/` directory

#### Tests
Execute the following script to run the full test suite for this project:

`./run_tests.sh`

#### Logging
To start logging to Datadog go to jenkins, techops jobs, create datadog log stream (for the desired env)  

| Field Name | Value |
| --- | --- |
| LOG_GROUP_PREFIX | `/aws/lambda/` |
| SERVICE | select your service |
| CUSTOM_NAME | create a custom name |

Logs can be found in [DataDog](https://app.datadoghq.com/logs?cols=%5B%22core_service%22%2C%22core_status%22%5D&from_ts=1531172170554&index=main&live=true&query=service%3Achalice-log&saved_view=1976&stream_sort=desc&to_ts=1531173070554) 
under `service:chalice-log`. 

NOTE:- Debug log can be verified on Cloudwatch. Datadog has a setting to exclude all debug logs, if the debug logs are needed in Datatog this setting needs to be disable. This settings controls log forward from all environments.

## Environment Variables

| Name | Data Type | Description | Format | Default |
| --- | --- | --- | --- | --- |
|`EXAMPLE_ENV_VAR`|`String`|Replace/Add accordingly|||
|`LOG_LEVEL`|`String`| Setting given log level to handle all events from that level on up. ||


## RESTful

*REMOVE THIS SECTION IF YOUR LAMBDA IS NOT BACKED BY 'AWS API Gateway'*

The REST tier is hosted via AWS API Gateway (`chalice-template`) and implemented by an AWS lambda.

#### URIs

| Environment | Host | Custom Domain Name |
| --- | --- | --- |
| `dev-us` | TBD | TBD |
| `stg-us` | TBD | TBD | 
| `prod` | TBD | TBD |

#### Endpoints

| Method | Url | Description |
| --- | --- | --- |
| POST | `/v1/events` | Accepts any JSON payload and places it on an SQS instance (verbatim)|

#### [GET `/health`]

Sample Request:
```sh
curl -i https://{host}/health 
```

Sample Response:
`{"status": "OK"}`

| Status Code | Description |
| --- | --- |
| `200 - Success` | Payload will report health status |
| `500 - InternalServiceError` | Uh oh... |
