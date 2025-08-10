from functools import wraps

from django.http import HttpRequest
from django.utils.translation import gettext as _
from oba import Obj

from smartdjango.code import Code
from smartdjango.error import Error
from smartdjango.utils import io
from smartdjango.validation.dict_validator import DictValidator
from smartdjango.validation.validator import Validator


class Request(HttpRequest):
    body: Obj
    query: Obj
    argument: Obj
    data: Obj


@Error.register
class AnalyseErrors:
    REQUEST_NOT_FOUND = Error(_("Cannot find request"), code=Code.InternalServerError)


def get_request(*args):
    for i, arg in enumerate(args):
        if isinstance(arg, HttpRequest):
            return arg
    raise AnalyseErrors.REQUEST_NOT_FOUND


def update_to_data(request: Request, target):
    data = getattr(request, '_data', None)
    data = data() if data is not None else {}
    data.update(target())
    request.data = Obj(data)


def analyse(*validators: Validator | str, target_getter, target_setter, restrict_keys):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = get_request(*args)
            target = target_getter(request, kwargs)

            validator = DictValidator().fields(*validators)
            if restrict_keys:
                validator.restrict_keys()
            target = validator.clean(target)
            target_setter(request, Obj(target))

            return func(*args, **kwargs)
        return wrapper
    return decorator


def body(*validators: Validator | str, restrict_keys=True):
    raise NotImplementedError('body is deprecated, use json instead')


def json(*validators: Validator | str, restrict_keys=True):
    def getter(request, kwargs):
        return io.json_loads(request.body.decode())

    def setter(request, target):
        request.json = target
        update_to_data(request, target)

    return analyse(
        *validators,
        target_getter=getter,
        target_setter=setter,
        restrict_keys=restrict_keys
    )


def query(*validators: Validator | str, restrict_keys=False):
    def getter(request, kwargs):
        return request.GET.dict()

    def setter(request, target):
        request.query = target
        update_to_data(request, target)

    return analyse(
        *validators,
        target_getter=getter,
        target_setter=setter,
        restrict_keys=restrict_keys
    )


def argument(*validators: Validator | str, restrict_keys=True):
    def getter(request, kwargs):
        return kwargs

    def setter(request, target):
        request.argument = target
        update_to_data(request, target)

    return analyse(
        *validators,
        target_getter=getter,
        target_setter=setter,
        restrict_keys=restrict_keys
    )


def request(bool_func, message=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = get_request(*args)
            Validator().bool(bool_func, message=message).clean(request)
            return func(*args, **kwargs)

        return wrapper
    return decorator
