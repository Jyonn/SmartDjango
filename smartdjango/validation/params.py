from typing import Type

from django.db import models

from smartdjango.validation.validator import Validator


class Params(type):
    model_class: Type[models.Model]
    __params = None

    @staticmethod
    def _handler_source(model_class, *attr_names):
        sources = []
        for attr_name in attr_names:
            source = getattr(model_class, attr_name, None)
            if source is not None:
                sources.append((attr_name, source))

        unique_sources = []
        for attr_name, source in sources:
            if all(existing is not source for _, existing in unique_sources):
                unique_sources.append((attr_name, source))

        if len(unique_sources) > 1:
            attr_names_str = ', '.join(name for name, _ in unique_sources)
            raise AttributeError(f'Conflicting params hook sources: {attr_names_str}')

        if not unique_sources:
            return None
        return unique_sources[0][1]

    @classmethod
    def _field_handler(cls, model_class, field_name, *attr_names):
        source = cls._handler_source(model_class, *attr_names)
        if source is None:
            return None
        handler = getattr(source, field_name, None)
        if callable(handler):
            return handler
        return None

    def __getattr__(cls, field_name):
        if cls.__params is None:
            cls.__params = {}

        if field_name not in cls.__params:
            field = cls.model_class._meta.get_field(field_name)
            validator = Validator.from_field(field, name=field.name, verbose_name=field.verbose_name)

            norm = cls._field_handler(cls.model_class, field_name, 'normalizers', 'normalizer', 'norm')
            if norm is not None:
                validator.to(norm)

            vldt = cls._field_handler(cls.model_class, field_name, 'validators', 'validator', 'vldt')
            if vldt is not None:
                validator.exception(vldt)

            cls.__params[field_name] = validator
        return cls.__params[field_name]
