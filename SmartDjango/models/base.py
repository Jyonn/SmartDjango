import datetime
import warnings
from typing import List, Tuple, Optional

from ..error import E
from ..http_code import HttpCode as Hc
from django.db import models
from smartify import Attribute, P, PError

from .manager import Manager
from . import fields


@E.register()
class ModelError:
    FIELD_FORMAT = E("Field format error", hc=Hc.Forbidden)


class Constraint:
    LENGTH_T = "{0}({1})'s length should not %s{2}"
    VALUE_T = "{0}({1}) should not %s{2}"

    def __init__(self, field, type_, boundary=True, compare=None, template=None):
        self.field, self.type, self.boundary = field, type_, boundary
        self.compare = compare or (lambda x: x)
        self.error_template = template or self.VALUE_T

    def fit(self, field, value):
        if isinstance(field, fields.CharField):
            max_, min_ = field.max_length, field.min_length
        else:
            max_, min_ = field.max_value, field.min_value
        if max_ and max_ < self.compare(value):
            raise ModelError.FIELD_FORMAT(append_message=(self.error_template % 'bigger').format(
                field.name, field.verbose_name, max_))
        if min_ and min_ > self.compare(value):
            raise ModelError.FIELD_FORMAT(append_message=(self.error_template % 'smaller').format(
                field.name, field.verbose_name, min_))


CONSTRAINTS = [
    Constraint(fields.CharField, str, compare=lambda x: len(x), template=Constraint.LENGTH_T),
    Constraint(fields.IntegerField, int),
    Constraint(fields.FloatField, float),
    Constraint(fields.BooleanField, bool, boundary=False),
    Constraint(fields.DateField, datetime.date),
    Constraint(fields.DateTimeField, datetime.datetime),
]


class Model(models.Model):
    objects = Manager()

    class Meta:
        abstract = True
        default_manager_name = 'objects'

    @classmethod
    def get_fields(cls, *field_names: str) -> Tuple[models.Field]:
        field_jar = dict()
        for field in cls._meta.fields:
            field_jar[field.name] = field

        field_list = []  # type: List[models.Field]
        for field_name in field_names:
            field_list.append(field_jar.get(field_name))

        return tuple(field_list)

    @classmethod
    def get_field(cls, field_name) -> models.Field:
        return cls.get_fields(field_name)[0]

    @classmethod
    def get_params(cls, *field_names: str):
        return tuple(map(cls.get_param, field_names))

    @classmethod
    def get_param(cls, field_name):
        field = cls.get_field(field_name)
        p = P(field.name, read_name=field.verbose_name)
        p.allow_null = field.null
        p.validate(Model.field_validator(field))
        return p

    P = get_params

    @staticmethod
    def field_validator(field: models.Field):
        attr = field.name
        verbose = field.verbose_name
        cls = field.model

        def validate(value):
            for constraint in CONSTRAINTS:
                if isinstance(field, constraint.field):
                    if not isinstance(value, constraint.type):
                        raise ModelError.FIELD_FORMAT(
                            append_message='%s(%s) has wrong type' % (attr, verbose))
                    if constraint.boundary:
                        constraint.fit(field, value)
                    break

            if field.choices:
                choice_match = False
                for choice in field.choices:
                    if value == choice[0]:
                        choice_match = True
                        break
                if not choice_match:
                    raise ModelError.FIELD_FORMAT(
                        append_message='%s(%s) is beyond choices' % (attr, verbose))

            custom_validator = getattr(cls, '_valid_%s' % attr, None)
            if callable(custom_validator):
                try:
                    custom_validator(value)
                except E as e:
                    raise e
                except Exception as err:
                    raise PError.VALIDATOR_CRUSHED(attr, verbose, debug_message=str(err))

        return validate

    @classmethod
    def validator(cls, attr_jar: dict):
        field_dict = dict()
        for field in cls._meta.fields:
            field_dict[field.name] = field

        for attr in attr_jar:
            attr_value = attr_jar[attr]
            if attr in field_dict:
                field = field_dict[attr]  # type: Optional[models.Field]
            else:
                field = None

            if field:
                try:
                    cls.field_validator(field)(attr_value)
                except E as e:
                    raise e
                except Exception as err:
                    raise PError.VALIDATOR_CRUSHED(attr, field.verbose_name, debug_message=str(err))
            else:
                custom_validator = getattr(cls, '_valid_%s' % attr, None)
                if callable(custom_validator):
                    try:
                        custom_validator(attr_value)
                    except E as e:
                        raise e
                    except Exception as err:
                        raise PError.VALIDATOR_CRUSHED(attr, attr, debug_message=str(err))

    def dictor(self, *field_list):
        warnings.warn(
            'dictor method is deprecated, use dictify instead.',
            DeprecationWarning)
        return self.dictify(*field_list)

    def dictify(self, *field_list):
        return Attribute.dictify(self, *field_list)
