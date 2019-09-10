import json
from functools import wraps

from django.http import HttpRequest

from .param import Param
from .packing import Packing
from .error import ErrorCenter, E
from .arg import get_arg_dict


class AnalyseError(ErrorCenter):
    TMP_METHOD_NOT_MATCH = E("请求方法错误", hc=400)
    TMP_REQUEST_TYPE = E('请求体类型错误', hc=400)


AnalyseError.register()


class Analyse:
    @staticmethod
    @Packing.pack
    def _validate_params(param_list, param_dict):
        result = dict()
        if not param_list:
            return result
        for param in param_list:
            if isinstance(param, str):
                param = Param(param)
            if isinstance(param, Param):
                value = param_dict.get(param.name)
                ret = param.run(value)
                if not ret.ok:
                    return ret
                result[param.yield_name or param.name] = ret.body
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
                ret = cls._validate_params(param_list, param_dict)
                if not ret.ok:
                    return ret
                return func(**param_dict)
            return wrapper
        return decorator

    @classmethod
    def r(cls, b=None, q=None, a=None, method=None):
        """
        decorator for validating HttpRequest
        :param b: Param list in it's BODY, in json format, without method in GET/DELETE
        :param q: Param list in it's query
        :param a: Param list in method/function argument
        :param method: Specify request method
        """
        def decorator(func):
            @wraps(func)
            def wrapper(r, *args, **kwargs):
                if not isinstance(r, HttpRequest):
                    return AnalyseError.TMP_REQUEST_TYPE
                if method and method != r.method:
                    return AnalyseError.TMP_METHOD_NOT_MATCH
                param_dict = dict()

                r.a_dict = get_arg_dict(func, args, kwargs)
                ret = cls._validate_params(a, r.a_dict)
                if not ret.ok:
                    return ret
                param_dict.update(ret.body or {})

                r.q_dict = r.GET.dict() or {}
                ret = cls._validate_params(q, r.q_dict)
                if not ret.ok:
                    return ret
                param_dict.update(ret.body or {})

                try:
                    r.b_dict = json.loads(r.body.decode())
                except json.JSONDecodeError:
                    r.b_dict = {}
                ret = cls._validate_params(b, r.b_dict)
                if not ret.ok:
                    return ret
                param_dict.update(ret.body or {})
                r.d = Param.Classify(param_dict)
                return func(r, *args, **kwargs)

            return wrapper

        return decorator
