from functools import wraps

from sqlalchemy.exc import NoSuchTableError


class APICallError(BaseException):
    pass


class ImproperlyConfigured(BaseException):
    pass


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