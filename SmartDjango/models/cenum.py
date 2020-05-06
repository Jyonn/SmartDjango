from enum import Enum


class CEnum(Enum):
    @classmethod
    def list(cls):
        return [(tag.name, tag.value) for tag in cls]
