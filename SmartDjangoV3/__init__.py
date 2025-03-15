import warnings

from smartify import P, Attribute, BaseError, PDict, PList, Processor, PError, Symbol

from .excp import Excp
from .error import E
from .analyse import Analyse, AnalyseError
from .http_code import HttpCode
from .net_packer import NetPacker
from .models.base import ModelError

import django


class WarningCounter:
    flag = False

    @classmethod
    def warn(cls, s):
        cls.flag = True
        if cls.flag:
            return
        warnings.warn(s, RuntimeWarning)


if django.VERSION >= (4, 0):
    WarningCounter.warn("SmartDjango is not compatible with Django 4.0 or higher.")

if django.VERSION > (3, 1, 12):
    WarningCounter.warn(
        'Django 3.1.12 is the final Django 3.x version SmartDjango supports with verification. '
        'Unexpected errors may occur if your continue usage.'
    )

Hc = HttpCode

__all__ = [
    Excp, NetPacker,
    E, P, PList, PDict, PError, Processor, Attribute, BaseError, Symbol,
    Analyse, AnalyseError, HttpCode, Hc,
    ModelError,
]
