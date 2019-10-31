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
                    return e
                e = None
            if isinstance(e, E):
                raise e
        except E as err:
            e = err

        from .excp import Excp
        return Excp.http_response(e)

    def process_exception(self, r, e):
        from .excp import Excp

        if isinstance(e, E):
            return Excp.http_response(e)
        else:
            return None
