import logging
import json
from uuid import uuid4


def init_logging(service_name: str, log_level: str):
    """Initialize logging to Datadog. This must be called before calling `logger.info`, etc.

    service_name: The name of this service for disambiguation in Datadog
    log_level: Any valid Python logging level from https://docs.python.org/3.8/library/logging.html#levels
    """
    log_level_upper = log_level.upper()
    request_id = str(uuid4())
    formatter = JsonFormatter(service_name, request_id)

    logger = logging.getLogger()
    logger.setLevel(log_level_upper)
    logger.handlers.clear()  # prevent double logging

    ch = logging.StreamHandler()
    ch.setLevel(log_level_upper)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class JsonFormatter(logging.Formatter):
    """Formats log messages for ingestion by Datadog."""
    def __init__(self, service_name: str, request_id: str):
        super().__init__()
        self.service_name = service_name
        self.request_id = request_id

    def format(self, record: logging.LogRecord):
        stack_info = None
        if getattr(record, 'exc_info', None):
            stack_info = super().formatException(record.exc_info)
        return json.dumps({
            'service': self.service_name,
            'request_id': self.request_id,
            'priority': record.levelname,
            'location': record.name,
            'stack_trace': stack_info,
            'message': record.getMessage(),
        })
