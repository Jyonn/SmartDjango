from django.db import models


class QuerySet(models.QuerySet):
    def map(self, func, *args, **kwargs):
        return [func(obj, *args, **kwargs) for obj in self]
