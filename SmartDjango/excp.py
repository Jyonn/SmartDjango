import json
from functools import wraps

from django.http import HttpResponse

from .error import BaseError, ETemplate, EInstance, ErrorCenter


class Excp(Exception):
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

    @staticmethod
    def handle(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                ret = Excp(func(request, *args, **kwargs))
            except Excp as e:
                ret = e
            return Excp.http_response(ret)
        return wrapper

    @staticmethod
    def http_response(o):
        ret = Excp(o)
        error = ret.error
        if error.append_msg:
            if error.e.ph == ETemplate.PH_NONE:
                msg = error.e.msg + '，%s' % error.append_msg
            elif error.e.ph == ETemplate.PH_FORMAT:
                msg = error.e.msg.format(*error.append_msg)
            else:
                msg = error.e.msg % error.append_msg
        else:
            msg = error.e.msg
        resp = dict(
            identifier=ErrorCenter.r_get(error.e.eid),
            code=error.e.eid,
            msg=msg,
            body=ret.body,
        )
        return HttpResponse(
            json.dumps(resp, ensure_ascii=False),
            status=error.e.hc,
            content_type="application/json; encoding=utf-8",
        )
