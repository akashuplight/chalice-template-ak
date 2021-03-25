from logging import getLogger

from chalice import Chalice, Response, BadRequestError, NotFoundError
from requests import HTTPError

from chalicelib.data.exceptions import ValidationError

LOGGER = getLogger(__name__)


class ChaliceRouterErrorHandler(Chalice):
    def _add_route(self, path, view_func, **kwargs):
        wrapped_view_func = self.error_handler(
                path=path, endpoint_function=view_func)
        super()._add_route(path, wrapped_view_func, **kwargs)

    def get_param(self, param_string):
        param_sent = self.current_request.query_params and self.current_request.query_params.get(param_string)
        if not param_sent:
            raise BadRequestError(
                self.current_request.method + ' requests to this endpoint must provide ' + param_string + ' parameter'
            )
        return param_sent

    def _log_problem(self, error_type, e, path):
        LOGGER.warning(f"Finished processing {self.current_request.method}"
                       f" request with body {self.current_request.json_body} with path {path}, "
                       f"but encountered a {error_type}: {e}", exc_info=True)

    def error_handler(self, path, endpoint_function):

        def decorated_ep_func(*original_args, **original_kwargs):
            try:
                return endpoint_function(*original_args, **original_kwargs)
            except BadRequestError as e:
                self._log_problem('BadRequestError', e, path)
                response_body = f"unable to service " + path + f" due to a bad request: {e}"
                return Response(status_code=400, body=response_body, headers={'Content-Type': 'application/json'})
            except ValidationError as e:
                self._log_problem('BadRequestError', e, path)
                response_body = f"unable to service " + path + f" due to a bad request: {e}"
                return Response(status_code=400, body=response_body, headers={'Content-Type': 'application/json'})
            except NotFoundError as e:
                self._log_problem('NotFoundError', e, path)
                response_body = f"unable to service " + path + f" due to a not found error: {e}"
                return Response(status_code=404, body=response_body, headers={'Content-Type': 'application/json'})
            except HTTPError as e:
                self._log_problem('HTTPError', e, path)
                response_body = f"unable to service " + path + f" due to a http error: {e}"
                return Response(status_code=e.response.status_code,
                                body=response_body, headers={'Content-Type': 'application/json'})
            except Exception as e:
                self._log_problem('Uncaught Exception', e, path)
                response_body = f"unable to service " + path + f" due to an internal error: {e}"
                return Response(status_code=500, body=response_body, headers={'Content-Type': 'application/json'})

        return decorated_ep_func
