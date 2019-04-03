import re

from django.db import models

from error import BaseError
from packing import Packing
from model import SmartModel


class Param:
    def __init__(self, param, verbose_name=None):
        self.param = param
        self.verbose_name = verbose_name or param
        self.valid_func = []
        self.default = None
        self.process_func = []

    @staticmethod
    def from_field(field):
        if not isinstance(field, models.Field):
            return None
        param = Param(field.name, field.verbose_name)

        if isinstance(field, models.CharField):
            param.valid_func.append(SmartModel.char_validator(field))
        if field.choices:
            param.valid_func.append(SmartModel.choice_validator(field))

    @Packing.pack
    def do(self, value=None):
        value = value or self.default
        for func in self.valid_func:
            if isinstance(func, str):
                if not re.match(func, value):
                    return BaseError.FIELD_FORMAT(self.verbose_name)
            elif callable(func):
                try:
                    ret = func(value)
                    if not ret.ok:
                        return ret
                except Exception:
                    return BaseError.FIELD_VALIDATOR

        for process in self.process_func:
            if callable(process):
                try:
                    value = process(value)
                except Exception:
                    return BaseError.FIELD_PROCESSOR
        return value
