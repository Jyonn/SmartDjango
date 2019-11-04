import json

from .middleware import HttpPackMiddleware
from django.http import HttpResponse
from smartify import BaseError

from .error import E
from .http_code import HttpCode as Hc


@E.register()
class PackerError:
    HTTP_DATA_PACKER = E("Http data packer crashed", hc=Hc.InternalServerError)


class NetPacker:
    fixed_code = False
    debug = True
    data_packer = None

    @staticmethod
    def pack(get_response):
        return HttpPackMiddleware(get_response)

    @classmethod
    def send(cls, o, using_data_packer=True):
        body, e = (None, o) if isinstance(o, E) else (o, BaseError.OK())

        resp = e.d_debug() if cls.debug else e.d()
        resp['body'] = body

        if using_data_packer and cls.data_packer:
            try:
                resp = cls.data_packer(resp)
            except Exception as err:
                return cls.send(
                    PackerError.HTTP_DATA_PACKER(debug_message=err), using_data_packer=False)

        return HttpResponse(
            json.dumps(resp, ensure_ascii=False),
            status=cls.fixed_code or e.hc,
            content_type="application/json; encoding=utf-8",
        )

    @classmethod
    def customize(cls, fixed_http_code=None, data_packer=None):
        cls.fixed_code = int(fixed_http_code)
        cls.data_packer = data_packer if callable(data_packer) else None

    @classmethod
    def set_mode(cls, debug=False):
        cls.debug = debug
