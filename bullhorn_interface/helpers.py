from functools import wraps

from sqlalchemy.exc import NoSuchTableError


class APICallError(BaseException):
    pass


class ImproperlyConfigured(BaseException):
    pass
