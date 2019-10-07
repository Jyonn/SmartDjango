from django.http import HttpResponse


class HttpPackMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, r, *args, **kwargs):
        from .excp import Excp

        try:
            ret = self.get_response(r, *args, **kwargs)
            if isinstance(ret, HttpResponse):
                if ret.content.decode().find(
                        "didn't return an HttpResponse object. It returned None instead.") == -1:
                    return ret
                ret = None
            ret = Excp(ret)
        except Excp as e:
            ret = e
        return Excp.http_response(ret)

    def process_exception(self, r, excp):
        from .excp import Excp
        if isinstance(excp, Excp):
            return Excp.http_response(excp)
        else:
            return None
