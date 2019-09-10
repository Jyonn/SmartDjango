from typing import Optional, Any, List, Callable, Tuple

from django.db import models

from SmartDjango import Packing, BaseError
from .models import Model


class P:
    class __NoDefault:
        pass

    class Classify:
        def dict(self, *args):
            if args:
                dict_ = dict()
                for k in args:
                    dict_[k] = self._dict.get(k)
                return dict_
            return self._dict

        def __init__(self, d):
            if not isinstance(d, dict):
                return
            self._dict = d

        def __getattr__(self, item):
            return self._dict.get(item)

    class Processor:
        def __init__(self,
                     processor: Callable,
                     only_validate: bool = False,
                     yield_name: Optional[str] = None):
            self.processor = processor
            self.only_validate = only_validate
            self.yield_name = yield_name

    def __init__(self, name: str, read_name: Optional[str] = None):
        self.name = name  # type:
        self.read_name = read_name or name

        self.null = False  # type: bool
        self.default = self.__NoDefault()  # type: Any

        self.dict = False  # type: bool
        self.list = False  # type: bool
        self.children = []  # type: List[P]

        self.processors = []  # type: List[P.Processor]

    def set_null(self, null: bool):
        self.null = null
        return self

    def set_default(self, value: Any = None, allow_default=True):
        if allow_default:
            self.default = value
        else:
            self.default = self.__NoDefault()
        return self

    def as_dict(self, children: List['P']):
        self.dict = True
        self.list = False
        self.children = children
        return self

    def as_list(self, children: List['P']):
        self.list = True
        self.dict = False
        self.children = children
        return self

    def process(self, processor: Processor, begin=False):
        if begin:
            self.processors.insert(0, processor)
        else:
            self.processors.append(processor)
        return self

    def validate(self, validator: Callable, begin=False):
        if begin:
            self.processors.insert(0, P.Processor(validator, only_validate=True))
        else:
            self.processors.append(P.Processor(validator, only_validate=True))
        return self

    @staticmethod
    def from_field(field: models.Field):
        p = P(field.name, read_name=field.verbose_name)
        p.null = field.null
        p.validate(Model.field_validator(field))
        return p

    @staticmethod
    def from_fields(fields: Tuple[models.Field]) -> Tuple['P']:
        return tuple(map(P.from_field, fields))

    def clone(self):
        p = P(self.name, self.read_name)

        p.null = self.null
        p.default = self.default

        p.dict = self.dict
        p.list = self.list
        p.children = self.children[:]

        p.processors = self.processors[:]

        return p

    def has_default(self):
        return not isinstance(self.default, self.__NoDefault)

    @Packing.pack
    def run(self, value):
        if value is None:
            if self.null:
                return None
            if self.has_default():
                value = self.default
            else:
                return BaseError.MISS_PARAM((self.name, self.read_name))

        if self.dict:
            # as a dict
            if not isinstance(value, dict):
                return BaseError.FIELD_FORMAT('%s(%s)不存在子参数' % (self.name, self.read_name))
            for p in self.children:
                child_value = value.get(p.name)
                child_yield_name, child_new_value = p.run(child_value).body
                if child_yield_name != p.name:
                    del value[p.name]
                value.setdefault(child_yield_name, child_new_value)
        elif self.list:
            # as a list
            if not isinstance(value, list):
                return BaseError.FIELD_FORMAT('%s(%s)不是列表' % (self.name, self.read_name))
            p = P('%s/child' % self.name, read_name='%s/子元素' % self.read_name).as_dict(self.children)
            new_value = []
            for child_value in value:
                child_yield_name, child_new_value = p.run(child_value)
                new_value.append(child_new_value)
            value = new_value

        yield_name = self.name
        for processor in self.processors:
            if processor.only_validate:
                # as a validator
                try:
                    processor.processor(value)
                except Packing as ret:
                    return ret
                except Exception:
                    return BaseError.FIELD_VALIDATOR('%s(%s)校验函数崩溃' %
                                                     (self.name, self.read_name))
            else:
                # as a processor
                try:
                    ret = processor.processor(value)
                except Packing as ret:
                    return ret
                except Exception:
                    return BaseError.FIELD_PROCESSOR('%s(%s)处理函数崩溃' %
                                                     (self.name, self.read_name))
                yield_name = processor.yield_name or yield_name
                if isinstance(ret, Packing):
                    value = ret.body
                else:
                    value = ret

        return yield_name, value
