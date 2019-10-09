import json
from functools import wraps

from django.http import HttpRequest

from .p import P
from .excp import Excp
from .error import ErrorJar, E
from .arg import get_arg_dict


@ErrorJar.pour
class AnalyseError:
    AE_METHOD_NOT_MATCH = E("请求方法错误", hc=400)
    AE_REQUEST_NOT_FOUND = E("找不到请求", hc=500)


class Analyse:
    @staticmethod
    @Excp.pack
    def process_params(param_list, param_dict):
        result = dict()
        if not param_list:
            return result
        for p in param_list:
            if isinstance(p, str):
                p = P(p)
            if isinstance(p, P):
                value = param_dict.get(p.name)
                yield_name, new_value = p.run(value)
                result[yield_name] = new_value
        return result

    @classmethod
    def p(cls, *param_list):
        """
        decorator for validating arguments in a method or a function
        :param param_list: a list of Param
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                param_dict = get_arg_dict(func, args, kwargs)
                cls.process_params(param_list, param_dict)
                return func(**param_dict)
            return wrapper
        return decorator

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
                    return AnalyseError.AE_REQUEST_NOT_FOUND
                if method and method != r.method:
                    return AnalyseError.AE_METHOD_NOT_MATCH
                param_jar = dict()

                a_dict = kwargs or {}
                result = cls.process_params(a, a_dict)
                param_jar.update(result or {})

                q_dict = r.GET.dict() or {}
                result = cls.process_params(q, q_dict)
                param_jar.update(result or {})

                try:
                    b_dict = json.loads(r.body.decode())
                except json.JSONDecodeError:
                    b_dict = {}
                result = cls.process_params(b, b_dict)
                param_jar.update(result or {})
                r.d = P.Classify(param_jar)
                return func(r)

            return wrapper

        return decorator
