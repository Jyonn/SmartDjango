from django.db.models.fields import *


class CharField(CharField):
    def __init__(self, *, min_length=None, **kwargs):
        self.min_length = min_length
        super().__init__(**kwargs)


class FloatField(FloatField):
    def __init__(self, *, max_value=None, min_value=None, **kwargs):
        self.max_value, self.min_value = max_value, min_value
        super().__init__(**kwargs)


class IntegerField(IntegerField):
    def __init__(self, *, max_value=None, min_value=None, **kwargs):
        self.max_value, self.min_value = max_value, min_value
        super().__init__(**kwargs)


class PositiveIntegerField(PositiveIntegerField, IntegerField):
    pass


class PositiveSmallIntegerField(PositiveSmallIntegerField, IntegerField):
    pass


class SmallIntegerField(SmallIntegerField, IntegerField):
    pass


class BigIntegerField(BigIntegerField, IntegerField):
    pass


class DateField(DateField):
    def __init__(self, *, max_value=None, min_value=None, **kwargs):
        self.max_value, self.min_value = max_value, min_value
        super().__init__(**kwargs)


class TimeField(TimeField):
    def __init__(self, *, max_value=None, min_value=None, **kwargs):
        self.max_value, self.min_value = max_value, min_value
        super().__init__(**kwargs)


class DateTimeField(DateTimeField, DateField):
    pass


__all__ = [
    'AutoField', 'BLANK_CHOICE_DASH', 'BigAutoField', 'BigIntegerField',
    'BinaryField', 'BooleanField', 'CharField', 'CommaSeparatedIntegerField',
    'DateField', 'DateTimeField', 'DecimalField', 'DurationField',
    'EmailField', 'Empty', 'Field', 'FieldDoesNotExist', 'FilePathField',
    'FloatField', 'GenericIPAddressField', 'IPAddressField', 'IntegerField',
    'NOT_PROVIDED', 'NullBooleanField', 'PositiveIntegerField',
    'PositiveSmallIntegerField', 'SlugField', 'SmallIntegerField', 'TextField',
    'TimeField', 'URLField', 'UUIDField',
]
