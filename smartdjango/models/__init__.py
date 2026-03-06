from diq import Dictify
from django.db.models import *
from django.db.models import Model as BaseModel

from smartdjango.models.queryset import QuerySet
from smartdjango.models.manager import Manager


class Model(BaseModel, Dictify):
    objects = Manager()

    class Meta:
        abstract = True
        default_manager_name = 'objects'
