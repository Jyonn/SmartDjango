import json
from functools import wraps

from django.http import HttpResponse
from smartify import BaseError

from .middleware import HttpPackMiddleware
from .error import E


@E.register()
class ExcpError:
    HTTP_DATA_PACKER = E("Http data packer crashed")


class Excp:
    http_response_always = False
    data_packer = None

    @staticmethod
    def pack(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            e = func(*args, **kwargs)
            if isinstance(e, E):
                raise e
            return e
        return wrapper

    handle = HttpPackMiddleware

    @classmethod
    def http_response(cls, o, using_data_packer=True):
        if isinstance(o, E):
            body = None
            e = o
        else:
            body = o
            e = BaseError.OK()
        resp = dict(
            identifier=e.identifier,
            code=e.eid,
            msg=e.message,
            body=body,
        )
        if using_data_packer and cls.data_packer:
            try:
                resp = cls.data_packer(resp)
            except Exception as err:
                return cls.http_response(
                    ExcpError.HTTP_DATA_PACKER(debug_message=err), using_data_packer=False)

        return HttpResponse(
            json.dumps(resp, ensure_ascii=False),
            status=cls.http_response_always or e.hc,
            content_type="application/json; encoding=utf-8",
        )

    @classmethod
    def custom_http_response(cls, http_code_always=None, data_packer=None):
        cls.http_response_always = int(http_code_always)
        cls.data_packer = data_packer if callable(data_packer) else None
