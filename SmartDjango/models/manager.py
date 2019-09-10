from django.db import models

from .query import QuerySet


class Manager(models.Manager):
    def __init__(self):
        super().__init__()
        self.restrict_args = tuple()
        self.restrict_kwargs = dict()

    def get_queryset(self):
        return QuerySet(self.model, using=self._db).filter(*self.restrict_args,
                                                           **self.restrict_kwargs)

    def restrict(self, *args, **kwargs):
        self.restrict_args = args
        self.restrict_kwargs = kwargs
        return self

    def search(self, *args, **kwargs):
        return self.all().search(*args, **kwargs)

    def dict(self, dictor):
        return self.all().dict(dictor)

    def page(self, pager, last=0, count=5):
        return pager.page(self.all(), last=last, count=count)
