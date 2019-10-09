import json
from functools import wraps

from django.http import HttpResponse

from .middleware import HttpPackMiddleware
from .error import BaseError, ETemplate, EInstance, ErrorJar


class Excp(Exception):
    http_response_always = False
    data_packer = None

    """
    函数返回类（规范）
    用于模型方法、路由控制方法等几乎所有函数中
    """

    def __init__(self, *args, **kwargs):
        """
        函数返回类构造器，根据变量个数判断
        """
        if not args:
            self.error = BaseError.OK
        else:
            arg = args[0]
            if isinstance(arg, ETemplate):
                self.error = arg()
            elif isinstance(arg, EInstance):
                self.error = arg
            elif isinstance(arg, Excp):
                self.error = arg.error
                self.body = arg.body
                self.extend = arg.extend
            else:
                self.error = BaseError.OK()
                self.body = args[0]
        self.extend = self.extend or kwargs

    def __getattribute__(self, item):
        try:
            return object.__getattribute__(self, item)
        except AttributeError:
            return None

    def __str__(self):
        return 'Ret(error=%s, body=%s, extend=%s)' % (self.error, self.body, self.extend)

    @property
    def ok(self):
        return self.error.e.eid == BaseError.OK.eid

    def erroris(self, e):
        return self.error.e.eid == e.eid

    eis = erroris

    @staticmethod
    def pack(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ret = func(*args, **kwargs)
            excp = Excp(ret)
            if not excp.ok:
                raise excp
            return ret
        return wrapper

    handle = HttpPackMiddleware

    @classmethod
    def http_response(cls, o, using_data_packer=True):
        ret = Excp(o)
        error = ret.error
        resp = dict(
            identifier=ErrorJar.get_i(error),
            code=error.e.eid,
            msg=error.get_msg(),
            body=ret.body,
        )
        if using_data_packer:
            try:
                resp = cls.data_packer(resp)
            except Exception:
                return cls.http_response(BaseError.HTTP_DATA_PACKER, using_data_packer=False)
        return HttpResponse(
            json.dumps(resp, ensure_ascii=False),
            status=cls.http_response_always or error.e.hc,
            content_type="application/json; encoding=utf-8",
        )

    @classmethod
    def custom_http_response(cls, http_code_always=None, data_packer=None):
        cls.http_response_always = int(http_code_always)
        cls.data_packer = data_packer if callable(data_packer) else None
