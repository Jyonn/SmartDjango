import json
from functools import wraps

from django.http import HttpRequest

from .p import P
from .excp import Excp
from .error import ErrorCenter, E
from .arg import get_arg_dict


class AnalyseError(ErrorCenter):
    TMP_METHOD_NOT_MATCH = E("请求方法错误", hc=400)


AnalyseError.register()


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
            def wrapper(r: HttpRequest, *args, **kwargs):
                if method and method != r.method:
                    return AnalyseError.TMP_METHOD_NOT_MATCH
                param_jar = dict()

                r.a_dict = get_arg_dict(func, args, kwargs)
                result = cls.process_params(a, r.a_dict)
                param_jar.update(result or {})

                r.q_dict = r.GET.dict() or {}
                result = cls.process_params(q, r.q_dict)
                param_jar.update(result or {})

                try:
                    r.b_dict = json.loads(r.body.decode())
                except json.JSONDecodeError:
                    r.b_dict = {}
                result = cls.process_params(b, r.b_dict)
                param_jar.update(result or {})
                r.d = P.Classify(param_jar)
                return func(r, *args, **kwargs)

            return wrapper

        return decorator
