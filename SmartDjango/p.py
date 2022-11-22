from typing import Optional, Any, List, Callable, Union

from django.db import models

from .excp import Excp
from .error import BaseError
from .models import Model


class P:
    """
    参数类，用于对函数参数的检测
    """
    class __NoDefault:
        pass

    class Processor:
        def __init__(self,
                     processor: Callable,
                     only_validate: bool = False,
                     yield_name: Optional[str] = None):
            self.processor = processor
            self.only_validate = only_validate
            self.yield_name = yield_name

    def __init__(self,
                 name: str,
                 read_name: Optional[str] = None,
                 yield_name: Optional[str] = None):
        self.name = name  # 参数名称
        self.read_name = read_name or name  # 参数可读名称
        self.yield_name = yield_name or name  # 参数返回名称，等级小于Processor的yield_name

        self.null = False  # type: bool
        self.default = self.__NoDefault()  # type: Any
        self.default_through_processor = False

        self.dict = False  # type: bool
        self.list = False  # type: bool
        self.children = []  # type: List[P]

        self.processors = []  # type: List[P.Processor]

    def __str__(self):
        return 'Param(%s, %s)' % (self.name, self.read_name)

    def rename(self, name: str, read_name: str = None, yield_name: str = None,
               stay_none: bool = False):
        self.name = name
        self.read_name = read_name or (self.read_name if stay_none else name)
        self.yield_name = yield_name or (self.yield_name if stay_none else name)
        return self

    def set_null(self, null: bool = True):
        self.null = null
        return self

    def set_default(self, value: Any = None, allow_default: bool = True, through_processor=False):
        if allow_default:
            self.default = value
        else:
            self.default = self.__NoDefault()
        self.default_through_processor = through_processor
        return self

    def as_dict(self, *children: Union['P', str]):
        self.dict = True
        self.list = False
        self.children = list(map(lambda p: P(p) if isinstance(p, str) else p, children))
        return self

    def as_list(self, *children: Union['P', str]):
        self.list = True
        self.dict = False
        self.children = list(map(lambda p: P(p) if isinstance(p, str) else p, children))
        return self

    def process(self, processor: Union[Processor, Callable], begin=False):
        if not isinstance(processor, P.Processor):
            processor = P.Processor(processor)
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
    def from_field(field: models.Field) -> 'P':
        p = P(field.name, read_name=field.verbose_name)
        p.null = field.null
        p.validate(Model.field_validator(field))
        return p

    @staticmethod
    def from_fields(*fields: models.Field):
        return tuple(map(P.from_field, fields))

    def clone(self):
        p = P(self.name, self.read_name, self.yield_name)

        p.null = self.null
        p.default = self.default

        p.dict = self.dict
        p.list = self.list
        p.children = self.children[:]

        p.processors = self.processors[:]

        return p

    def has_default(self):
        return not isinstance(self.default, self.__NoDefault)

    @Excp.pack
    def run(self, value):
        yield_name = self.yield_name

        if value is None:
            if self.null:
                return yield_name, None
            if self.has_default():
                if not self.default_through_processor:
                    return yield_name, self.default
                else:
                    value = self.default
            else:
                return BaseError.MISS_PARAM((self.name, self.read_name))

        if self.dict:
            # as a dict
            if not isinstance(value, dict):
                return BaseError.FIELD_FORMAT('%s(%s)不存在子参数' % (self.name, self.read_name))
            for p in self.children:
                child_value = value.get(p.name)
                child_yield_name, child_new_value = p.run(child_value)
                if child_yield_name != p.name:
                    del value[p.name]
                value.setdefault(child_yield_name, child_new_value)
        elif self.list:
            # as a list
            if not isinstance(value, list):
                return BaseError.FIELD_FORMAT('%s(%s)不是列表' % (self.name, self.read_name))
            p = P('%s/child' % self.name, '%s/子元素' % self.read_name).as_dict(*self.children)
            new_value = []
            for child_value in value:
                child_yield_name, child_new_value = p.run(child_value)
                new_value.append(child_new_value)
            value = new_value

        for processor in self.processors:
            if processor.only_validate:
                # as a validator
                try:
                    processor.processor(value)
                except Excp as ret:
                    return ret
                except Exception:
                    return BaseError.FIELD_VALIDATOR('%s(%s)校验函数崩溃' %
                                                     (self.name, self.read_name))
            else:
                # as a processor
                try:
                    ret = processor.processor(value)
                except Excp as ret:
                    return ret
                except Exception:
                    return BaseError.FIELD_PROCESSOR('%s(%s)处理函数崩溃' %
                                                     (self.name, self.read_name))
                yield_name = processor.yield_name or yield_name
                value = ret

        return yield_name, value
