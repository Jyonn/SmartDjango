import warnings

from django.http import HttpResponse
from smartify import E


class HttpPackMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, r, *args, **kwargs):
        try:
            e = self.get_response(r, *args, **kwargs)
            if isinstance(e, HttpResponse):
                if e.content.decode().find(
                        "t return an HttpResponse object. It returned None instead.") == -1:
                    warnings.warn('Please return a Not-None value', DeprecationWarning)
                    return e
                e = None
            if isinstance(e, E):
                raise e
        except E as err:
            e = err

        from .net_packer import NetPacker
        return NetPacker.send(e)

    def process_exception(self, _, e):
        from .net_packer import NetPacker
        if isinstance(e, E):
            return NetPacker.send(e)
        else:
            return None
