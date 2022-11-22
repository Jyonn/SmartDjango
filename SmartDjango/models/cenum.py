from enum import Enum


class CEnum(Enum):
    @classmethod
    def list(cls):
        return [(tag.name, tag.value) for tag in cls]


class CREnum(Enum):
    @classmethod
    def list(cls):
        return [(tag.value, tag.name) for tag in cls]
