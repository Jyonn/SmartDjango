from typing import Dict, Optional, Union

from django.utils.encoding import force_str
from django.utils.functional import Promise

from smartdjango.code import Code


MessageLike = Union[str, Promise]


class Error(Exception):
    __ERRORS: Dict[str, 'Error'] = dict()

    """Base class for exceptions in this module."""
    def __init__(
        self,
        message: MessageLike,
        code=Code.OK,
        user_message: Optional[MessageLike] = None,
        identifier=None,
    ):
        super().__init__(message)

        self.__identifier = identifier or None
        self.message = message
        self.code = code
        self.details = []
        self.user_message = user_message or message

    @property
    def identifier(self) -> str:
        return self.__identifier

    @identifier.setter
    def identifier(self, value):
        if self.__identifier is not None:
            raise AttributeError('Identifier is already set')
        if value in self.__ERRORS:
            raise AttributeError(f'Conflict error identifier: {value}')
        self.__identifier = value
        self.__ERRORS[value] = self

    def json(self):
        return {
            'message': force_str(self.message),
            'code': self.code,
            'details': self.details,
            'user_message': force_str(self.user_message),
            'identifier': self.identifier,
        }

    def jsonl(self):
        return {
            'message': force_str(self.message),
            'code': self.code,
            'identifier': self.identifier,
        }

    def __call__(self, details=None, user_message=None, **kwargs):
        message = force_str(self.message).format(**kwargs)
        if user_message is None:
            user_message = force_str(self.user_message).format(**kwargs)

        if details is not None and not isinstance(details, str):
            details = force_str(details)
        if user_message is not None and not isinstance(user_message, str):
            user_message = force_str(user_message)
        error = Error(message, code=self.code, user_message=user_message, identifier=self.identifier)
        error.details = self.details.copy()
        if details is not None:
            error.details.append(details)
        return error

    def __eq__(self, other: 'Error'):
        return self.identifier == other.identifier

    @classmethod
    def register(cls, class_):
        class_name = class_.__name__
        if not class_name.upper().endswith('ERRORS'):
            raise AttributeError('Error class name should end with "Errors"')
        class_name = class_name[:-6].upper()
        for name in class_.__dict__:  # type: str
            e = getattr(class_, name)
            if not isinstance(e, Error):
                continue
            e.identifier = f'{class_name}@{name}'

        return class_

    def ok(self) -> bool:
        return self.identifier == 'OK'

    @classmethod
    def all(cls) -> Dict[str, 'Error']:
        return cls.__ERRORS

    def equals(self, other: 'Error'):
        return self.identifier == other.identifier


OK = Error('OK', code=Code.OK, identifier='OK')
