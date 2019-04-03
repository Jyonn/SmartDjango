import json
from functools import wraps

from django.http import HttpResponse

from error import BaseError, E, EInstance, ErrorDict


class Packing:
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
            if isinstance(arg, E):
                self.error = arg()
            elif isinstance(arg, EInstance):
                self.error = arg
            elif isinstance(arg, Packing):
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

    def ok(self):
        return self.error.e.eid == BaseError.OK.eid

    @staticmethod
    def pack(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return Packing(func(*args, **kwargs))
        return wrapper

    @staticmethod
    def http_pack(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ret = Packing(func(*args, **kwargs))
            error = ret.error
            resp = dict(
                identifier=ErrorDict.r_get(error.e.eid),
                code=error.e.eid,
                msg=error.e.msg + (('，%s' % error.append_msg) if error.append_msg else ''),
                body=ret.body,
            )
            return HttpResponse(
                json.dumps(resp, ensure_ascii=False),
                status=200,
                content_type="application/json; encoding=utf-8",
            )

        return wrapper
