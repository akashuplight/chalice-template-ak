import os, requests, datetime, json

from logging import getLogger
from chalice import Chalice, BadRequestError, NotFoundError, UnauthorizedError, ForbiddenError, ChaliceViewError

from chalicelib.annotations.timer import timer
from chalicelib.utils.datadog_utils import count
from chalicelib.utils.logging import init_logging

SERVICE_NAME = 'chalice-template'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

init_logging(SERVICE_NAME, LOG_LEVEL)
LOGGER = getLogger(__name__)

app = Chalice(app_name=SERVICE_NAME, debug=True)

BASE_URL = "https://dr-enrollment.mp.uat.simpleenergy.io/"


# Be sure @timer is after all @app.* annotations, otherwise it won't work
@app.route('/health')
@timer('health.response_time_ms', custom='tag')
def get_health():
    LOGGER.info('Health invoked.')
    count(metric='health.count', custom_a='tag', custom_b=1)
    return {'status': 'OK'}


def updated_enrollment_status(data):
    if "enrollment_state" in data and data["enrollment_state"] in ["enrolled" , "unenrolled"]:
        return "unenrolled" if data["enrollment_state"] == "enrolled" else "enrolled"


def handling_server_errors(status_code, type_req='GET'):
    if status_code >=200 and status_code <300:
        return
    elif status_code is 404:
        raise NotFoundError("Record not found!!")
    elif status_code is 403:
        raise ForbiddenError("Forbidden: You don't have permission to access!!")
    elif status_code is 401:
        raise UnauthorizedError("Unauthorized: You are not authorize!!!")
    elif status_code is 400:
        raise BadRequestError("BadRequest: 400")
    else:
        raise ChaliceViewError("Internal server error" if type_req=="GET" else "Internal error on POST request")


@app.route("/enrollment", methods=['POST'])
@timer('enrollment.response_time_ms', custom='tag')
def enrollment_status():
    body  = app.current_request.json_body
    if body.get('token', None) and body.get('enrollment_uuid', None):
        resp = requests.get(BASE_URL + "enrollment/" + body.get('enrollment_uuid'), headers={"x-api-key": body.get('token')})

        handling_server_errors(resp.status_code)
        data = resp.json()

        # using  UTC time zone
        payload = {
            "enrollment_state": updated_enrollment_status(data),
            "enrollment_date": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
        utc_time = datetime.datetime.utcnow()
        headers = {
            'x-api-key': body.get('token'),
            'content-type': "application/json"
        }
        resp = requests.post(BASE_URL + "enrollment/" + body.get('enrollment_uuid'), data=json.dumps(payload), headers=headers)
        handling_server_errors(resp.status_code, 'POST')
        return resp.json()

    else:
        raise BadRequestError(f"`token` and `enrollment_uuid` can't be empty!!")

# Here are a few more examples:
#
# This one enforces that a server-side API Gateway key be provided as a request header: x-api-key
# @app.route('/hello/{name}', api_key_required=True)
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples:
# https://chalice.readthedocs.io/en/latest/
