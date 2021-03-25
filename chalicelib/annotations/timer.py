from chalicelib.utils.datadog_utils import timer as datadog_timer, current_time_millis


def timer(metric, **custom_tags):
    def wrap(func):
        def wrap_func(*args, **kw):
            ts = current_time_millis()
            result = func(*args, **kw)
            datadog_timer(metric=metric, start=ts, **custom_tags)
            return result
        return wrap_func
    return wrap
