import json
from functools import wraps

from django.http import HttpRequest
from oba import Obj
from smartify import Analyse as BAnalyse, PDict, P

from .error import E
from .http_code import HttpCode as Hc


@E.register()
class AnalyseError:
    AE_METHOD_NOT_MATCH = E("Wrong request method", hc=Hc.InternalServerError)
    AE_REQUEST_NOT_FOUND = E("Can't find request", hc=Hc.InternalServerError)


class Analyse(BAnalyse):
    @classmethod
    def r(cls, b=None, q=None, a=None, method=None):
        """
        decorator for validating HttpRequest
        :param b: P list in it's BODY, in json format, without method in GET/DELETE
        :param q: P list in it's query
        :param a: P list in method/function argument
        :param method: Specify request method
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                r = None
                for v in args:
                    if isinstance(v, HttpRequest):
                        r = v
                        break
                if not r:
                    for k in kwargs:
                        if isinstance(kwargs[k], HttpRequest):
                            r = kwargs[k]
                            break
                if not r:
                    raise AnalyseError.AE_REQUEST_NOT_FOUND
                if method and method != r.method:
                    raise AnalyseError.AE_METHOD_NOT_MATCH
                param_jar = dict()

                a_dict = kwargs or {}
                q_dict = r.GET.dict() or {}
                try:
                    b_dict = json.loads(r.body.decode())
                except json.JSONDecodeError:
                    b_dict = {}

                checks = [(a, a_dict), (b, b_dict), (q, q_dict)]
                for check in checks:
                    if check[0]:
                        if isinstance(check[0], P):
                            p = check[0]
                        else:
                            p = PDict().set_fields(*check[0])
                        _, result = p.run(check[1])
                        param_jar.update(result or {})

                r.d = Obj(param_jar)
                return func(r)

            return wrapper

        return decorator
