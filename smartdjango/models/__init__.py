from diq import Dictify
from django.db import models

from smartdjango.models.queryset import QuerySet
from smartdjango.models.manager import Manager


class Model(models.Model, Dictify):
    objects = Manager()

    class Meta:
        abstract = True
        default_manager_name = 'objects'
