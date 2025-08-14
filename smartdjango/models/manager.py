# 自定义 Manager
from django.db import models

from smartdjango.models.queryset import QuerySet


class Manager(models.Manager):
    def get_queryset(self) -> QuerySet:
        return QuerySet(self.model, using=self._db)

    def map(self, func, *args, **kwargs):
        return self.get_queryset().map(func, *args, **kwargs)
