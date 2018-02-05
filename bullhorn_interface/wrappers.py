import functools, logging
from functools import wraps
from sqlalchemy.exc import NoSuchTableError

def depaginate_search(method):
    @wraps(method)
    def _impl(self, *method_args, **method_kwargs):
        desired_count, start = 500, 0
        if 'count' in list(method_kwargs.keys()):
            desired_count = method_kwargs.pop('count')
        if 'start' in list(method_kwargs.keys()):
            start = method_kwargs.pop('start')
        desired_count = int(desired_count)
        if desired_count < 500:
            # no need to do any depaginating
            response = method(self, *method_args, start=start, count=desired_count, **method_kwargs)
            return response
        else:
            # always request the maximum allowed for the initial response
            response = method(self, *method_args, start=start, count=500, **method_kwargs)
        if len(response["data"]) == 0:
            # don't do anything if the query is bad
            return response
        desired_total = min(response["total"]  - start, desired_count)
        response["start"] += response["count"]
        while response["count"] < desired_total:
            if desired_total - response["count"] < 500:
                temp_count = desired_total - response["count"]
            else:
                temp_count = 500
            temp_response = method(self, *method_args, start=response["start"], count=temp_count, **method_kwargs)
            response["data"].extend(temp_response["data"])
            response["count"] += temp_response["count"]
            response["start"] += temp_response["count"]
        response["start"] = start
        if self._serialize:
            try:
                from pandas.io.json import json_normalize
                response = json_normalize(response["data"])
            except ModuleNotFoundError:
                logging.error('pandas is required for serialization.')
        return  response
    return _impl

def depaginate_query(method):
    @wraps(method)
    def _impl(self, *method_args, **method_kwargs):
        desired_count, start = 500, 0
        if 'count' in list(method_kwargs.keys()):
            desired_count = method_kwargs.pop('count')
        if 'start' in list(method_kwargs.keys()):
            start = method_kwargs.pop('start')
        desired_count = int(desired_count)
        if desired_count < 500:
            # no need to do any depaginating
            response = method(self, *method_args, start=start, count=desired_count, **method_kwargs)
            return response
        else:
            # always request the maximum allowed for the initial response
            response = method(self, *method_args, start=start, count=500, **method_kwargs)
        if len(response["data"]) == 0:
            # don't do anything if the query is bad
            return response
        desired_total = desired_count
        response["start"] += response["count"]
        temp_response = response
        while temp_response["count"] == 500 and response["count"] < desired_count:
            if desired_total - response["count"] < 500:
                temp_count = desired_total - response["count"]
            else:
                temp_count = 500
            temp_response = method(self, *method_args, start=response["start"], count=temp_count, **method_kwargs)
            response["data"].extend(temp_response["data"])
            response["count"] += temp_response["count"]
            response["start"] += temp_response["count"]
        response["start"] = start
        if self._serialize:
            try:
                from pandas.io.json import json_normalize
                response = json_normalize(response["data"])
            except ModuleNotFoundError:
                logging.error('pandas is required for serialization.')
        return  response
    return _impl

def log_parameters(method):
    @wraps(method)
    def _impl(self, *method_args, **method_kwargs):
        if 'parameters' in self._debug:
            logger.warning(f'args: {method_args}\nkwargs: {method_kwargs}\n\n')
        response = method(self, *method_args, **method_kwargs)
        return  response
    return _impl


def no_such_table_handler(method):
    @wraps(method)
    def _impl(self, *method_args, **method_kwargs):
        try:
            result = method(self, *method_args, **method_kwargs)
        except NoSuchTableError:
            self.login()
            self.get_api_token()
            result = method(self, *method_args, **method_kwargs)
        return result
    return _impl

def wrap_method(cls, name, wrapper_method_name):
    # This unbound method will be pulled from the superclass.
    wrapped = getattr(cls, name, wrapper_method_name)

    @functools.wraps(wrapped)
    def wrapper(self, *args, **kwargs):
        wrapper_method = getattr(self, wrapper_method_name)
        return wrapper_method(wrapped.__get__(self, cls), *args, **kwargs)

    return wrapper


def wrap_methods(cls):
    for wrapper_method_name in cls.WRAPPER_METHOD_NAMES:
        for name in cls.WRAPPED_METHODS:
            setattr(cls, name, wrap_method(cls, name, wrapper_method_name))
    return cls