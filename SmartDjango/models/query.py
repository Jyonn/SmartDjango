from django.db import models
from django.db.models import Q


class QuerySet(models.QuerySet):
    def search(self, *args, **kwargs):
        objects = self.all()
        cls = self.model

        field_dict = dict()
        for o_field in cls._meta.fields:
            field_dict[o_field.name] = o_field

        for q in args:
            if isinstance(q, Q):
                objects = objects.filter(q)

        for attr in kwargs:
            attr_value = kwargs[attr]

            if attr.endswith('__null'):
                attr = attr[:-6]
            elif attr_value is None:
                continue

            full = attr.endswith('__full')
            if full:
                attr = attr[:-6]

            filter_func = getattr(cls, '_search_%s' % attr, None)
            if filter_func and callable(filter_func):
                o_filter = filter_func(attr_value)
                if isinstance(o_filter, dict):
                    objects = objects.filter(**o_filter)
                elif isinstance(o_filter, Q):
                    objects = objects.filter(o_filter)
                continue

            if attr in field_dict:
                attr_field = field_dict[attr]
            else:
                attr_field = None

            filter_dict = dict()
            if not full and \
                    (isinstance(attr_field, models.CharField) or
                     isinstance(attr_field, models.TextField)):
                filter_dict.setdefault('%s__contains' % attr, attr_value)
            else:
                filter_dict.setdefault(attr, attr_value)

            objects = objects.filter(**filter_dict)
        return objects

    def dict(self, dictor):
        if callable(dictor):
            return list(map(dictor, self))
        return self

    def page(self, pager, last=0, count=5):
        return pager.page(self, last=last, count=count)