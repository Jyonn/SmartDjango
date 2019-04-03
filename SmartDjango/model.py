from functools import wraps

import getclass
from django.db import models

from SmartDjango.arg import get_arg_dict
from SmartDjango.error import BaseError
from SmartDjango.packing import Packing


class SmartModel(models.Model):
    class Meta:
        abstract = True

    @staticmethod
    def __char_validator(field):
        @Packing.pack
        def _validator(value):
            if not isinstance(value, str):
                return BaseError.FIELD_FORMAT('%s类型错误', field.verbose_name)
            if field.max_length < len(value):
                return BaseError.FIELD_FORMAT(
                    '%s长度不应超过%s字符' % (field.verbose_name, field.max_length))
            return
        return _validator

    @staticmethod
    def __choice_validator(field):
        @Packing.pack
        def _validator(value):
            choice_match = False
            for choice in field.choices:
                if value is choice:
                    choice_match = True
                    break
            if not choice_match:
                return BaseError.FIELD_FORMAT
        return _validator

    @staticmethod
    @Packing.pack
    def __validator(cls, attr_dict):
        if not isinstance(attr_dict, dict):
            return BaseError.FIELD_VALIDATOR
        if not isinstance(cls, SmartModel):
            return BaseError.FIELD_VALIDATOR

        # 获取字段字典
        field_dict = dict()
        for local_field in cls._meta.local_fields:
            field_dict[local_field.attname] = local_field

        # 遍历传入的参数
        for attr in attr_dict.keys():
            attr_value = attr_dict[attr]
            if attr in field_dict:
                # 参数名为字段名
                attr_field = field_dict[attr]
                if not isinstance(attr_field, models.Field):
                    return BaseError.FIELD_VALIDATOR
                # CharField比较max_length
                if isinstance(attr_field, models.CharField):
                    ret = SmartModel.__char_validator(attr_field)(attr_value)
                    if ret.error is not BaseError.OK:
                        return ret
                # 存在choices判断是否越界
                if attr_field.choices:
                    ret = SmartModel.__choice_validator(attr_field)(attr_value)
                    if ret.error is not BaseError.OK:
                        return ret

                # 自定义函数
                valid_func = getattr(cls, '_valid_%s' % attr, None)
                if valid_func and callable(valid_func):
                    try:
                        ret = valid_func(attr_value)
                        if ret.error is not BaseError.OK:
                            return ret
                    except Exception:
                        return BaseError.FIELD_VALIDATOR('%s自定义校验函数崩溃', attr_field.verbose_name)
        return

    @staticmethod
    def _validator(cls):
        def decorator(func):
            @wraps(func)
            @Packing.pack
            def wrapper(*args, **kwargs):
                arg_dict = get_arg_dict(func, args, kwargs)
                ret = SmartModel.__validator(cls, arg_dict)
                if ret.error is not BaseError.OK:
                    return ret
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def __getattribute__(self, item):
        attr = object.__getattribute__(self, item)
        if not callable(attr) or item[0] == '_':
            return attr
        if hasattr(item, '__self__'):
            _class = getclass.getclass(attr.__self__)
        else:
            _class = getclass.getclass(attr)
        if hasattr(SmartModel.__dict__, item):
            return attr
        return object.__getattribute__(self, '_validator')(_class)(attr)

    def dictor(self, field_list, string=True):
        d = dict()
        for field in field_list:
            if not isinstance(field, models.Field):
                continue

            value = getattr(self, field.name, None)
            if string:
                readable_func = getattr(self, '_readable_%s' % field.name, None)
                if readable_func and callable(readable_func):
                    value = readable_func()
            d[field.name] = value
        return d
