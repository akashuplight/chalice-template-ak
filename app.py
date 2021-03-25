import os

from logging import getLogger
from chalice import Chalice

from chalicelib.annotations.timer import timer
from chalicelib.utils.datadog_utils import count
from chalicelib.utils.logging import init_logging

SERVICE_NAME = 'chalice-template'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

init_logging(SERVICE_NAME, LOG_LEVEL)
LOGGER = getLogger(__name__)

app = Chalice(app_name=SERVICE_NAME)


# Be sure @timer is after all @app.* annotations, otherwise it won't work
@app.route('/health')
@timer('health.response_time_ms', custom='tag')
def get_health():
    LOGGER.info('Health invoked.')
    count(metric='health.count', custom_a='tag', custom_b=1)
    return {'status': 'OK'}

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
