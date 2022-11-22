import warnings
from functools import wraps

from .net_packer import NetPacker
from .middleware import HttpPackMiddleware
from .error import E


class Excp:
    @staticmethod
    def pack(func):
        warnings.warn(
            'Excp.pack is deprecated, use "raise XXError.xx" instead of "return XXError.xx".',
            DeprecationWarning)

        @wraps(func)
        def wrapper(*args, **kwargs):
            e = func(*args, **kwargs)
            if isinstance(e, E):
                raise e
            return e
        return wrapper

    # handle = HttpPackMiddleware
    @staticmethod
    def handle(get_response):
        warnings.warn(
            'Excp.handle is deprecated, use NetPacker.pack instead.',
            DeprecationWarning)
        return HttpPackMiddleware(get_response)

    @classmethod
    def http_response(cls, o, using_data_packer=True):
        warnings.warn(
            'Excp.http_response is deprecated, use NetPacker.send instead.',
            DeprecationWarning)
        return NetPacker.send(o, using_data_packer=using_data_packer)

    @classmethod
    def custom_http_response(cls, http_code_always=None, data_packer=None):
        warnings.warn(
            'Excp.custom_http_response is deprecated, use NetPacker.customize instead.',
            DeprecationWarning)
        NetPacker.customize(http_code_always, data_packer)

    @classmethod
    def debugging(cls, off=False):
        warnings.warn(
            'Excp.debugging is deprecated, use NetPacker.set_mode instead.',
            DeprecationWarning)
        NetPacker.set_mode(debug=not off)
