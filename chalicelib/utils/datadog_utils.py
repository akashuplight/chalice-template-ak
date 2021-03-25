import logging
import os

from time import time

tendril_env = os.getenv('TENDRIL_ENV', 'dev-us')

# From https://docs.datadoghq.com/integrations/amazon_lambda/
# MONITORING|<unix_epoch_timestamp>|<value>|<metric_type>|<metric_name>|#<tag_list>
datadog_log_message_template = "MONITORING|{}|{}|{}|{}|#{}"

tags = ['env:{}'.format(tendril_env), 'service:test-datadog-chalice']


def current_time_millis():
    return int(round(current_time_seconds() * 1000))


def current_time_seconds():
    return time()


def append_custom_tags(custom_tags_dict):
    all_tags = tags.copy()

    for key, val in custom_tags_dict.items():
        all_tags.append(f'{key}:{val}')
    return all_tags


def timer(metric, start, end=None, **custom_tags):
    now_millis = current_time_millis()
    time_delta = (end if end is not None else now_millis) - start

    request_tags = append_custom_tags(custom_tags)

    logging.info(datadog_log_message_template.format(
        int(round(current_time_seconds())),
        time_delta,
        'histogram',
        metric,
        str.join(',', request_tags)))


def count(metric, incr=1, **custom_tags):
    request_tags = append_custom_tags(custom_tags)
    logging.info(datadog_log_message_template.format(
        int(round(current_time_seconds())),
        incr,
        'count',
        metric,
        str.join(',', request_tags)))


def gauge(metric, value, **custom_tags):
    request_tags = append_custom_tags(custom_tags)
    logging.info(datadog_log_message_template.format(
        int(round(current_time_seconds())),
        value,
        'gauge',
        metric,
        str.join(',', request_tags)))
