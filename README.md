# smartdjango

High-level utilities for Django APIs: response packing, structured errors, request/argument validation, and small ORM helpers.

## Install

```
pip install smartdjango
```

Requires Django. Some features use `oba` (`Obj`) for attribute access.

## Quick start

### 1) Pack API responses

Add the middleware and return plain data or `Error` objects from views.

```python
# settings.py
MIDDLEWARE = [
    # ...
    "smartdjango.middleware.APIPacker",
]
```

```python
from smartdjango import Error, Code

class Errors:
    INVALID = Error("Invalid", code=Code.BadRequest, identifier="INVALID")


def handler(request):
    if not request.user.is_authenticated:
        return Errors.INVALID
    return {"ok": True}
```

`APIPacker` behavior:
- If the view returns a `django.http.HttpResponse`, it is passed through.
- If the view returns an `Error`, it is serialized with `error.json()` and HTTP status = `error.code`.
- Otherwise, the response is wrapped as `{"message", "code", "details", "user_message", "identifier", "body"}` with `OK`.

### 2) Structured errors

```python
from smartdjango import Error, Code

@Error.register
class UserErrors:
    NOT_FOUND = Error("User not found", code=Code.NotFound)
    INVALID_EMAIL = Error("Invalid email", code=Code.BadRequest)
```

`Error.register` assigns unique identifiers like `USER@NOT_FOUND`.

## Validation

### Validator

```python
from smartdjango import Validator

validator = Validator("age").bool(lambda v: isinstance(v, int), message="Not an int")
validator.clean(10)
```

Features:
- `null(allow_null=True)` to allow `None`.
- `default(value, as_final=False)` to provide defaults.
- `to(func)` to cast/normalize.
- `bool(func, message=...)` and `exception(func, message=...)` for validation.
- `Validator.from_field(model_field)` builds a validator from a Django model field.

### DictValidator

```python
from smartdjango import DictValidator, Validator

validator = (
    DictValidator()
    .fields(
        Validator("name").bool(lambda v: isinstance(v, str), message="Not a string"),
        Validator("age").bool(lambda v: isinstance(v, int), message="Not an int"),
    )
    .restrict_keys()
)

cleaned = validator.clean({"name": "Ada", "age": 18})
```

- `restrict_keys()` rejects extra keys.
- Uses `Key` to rename outputs via `final_name` when desired.

### ListValidator

```python
from smartdjango import ListValidator, Validator

validator = ListValidator().element(Validator().bool(lambda v: isinstance(v, int)))
cleaned = validator.clean([1, 2, 3])
```

- `element(validator)` applies the same validator to each element.
- `elements(v1, v2, ...)` validates a fixed-length list.

### Model params

```python
from smartdjango import Params
from myapp.models import User

class UserParams(metaclass=Params):
    model_class = User

name_validator = UserParams.username  # derived from model field
```

`Params` lazily creates validators from Django model fields.

## Request/argument analysis

Decorators in `smartdjango.analyse` validate and attach cleaned data.

```python
from smartdjango import analyse, Validator

@analyse.json(Validator("name"))
def create_user(request):
    # request.json is an Obj
    name = request.json.name
    return {"name": name}
```

Available decorators:
- `analyse.json(*validators, restrict_keys=True)` reads `request.body` as JSON.
- `analyse.query(*validators, restrict_keys=False)` reads `request.GET`.
- `analyse.argument(*validators, restrict_keys=True)` validates view kwargs.
- `analyse.function(*validators, restrict_keys=True)` validates function args/kwargs.
- `analyse.request(bool_func, message=None)` validates a `HttpRequest` itself.

All decorators raise `Error` (from validators) on failure.

## Pagination

```python
from smartdjango.paginator import Paginator

p = Paginator(queryset, page_size=20)
page = p.get_page(page=0)

payload = page.dict(lambda obj: {"id": obj.id})
```

Cursor-style pagination is supported via `filter(field__lt=value)` or `filter(field__gt=value)`,
then calling `get_page(page=None)`.

## ORM helpers

```python
from smartdjango.models import Manager

class User(models.Model):
    objects = Manager()

# map across queryset
users = User.objects.filter(is_active=True).map(lambda u: u.username)
```

## Utilities

- `smartdjango.choice.Choice.to_choices()` turns class attributes into Django choices.
- `smartdjango.utils.io` provides JSON and pickle helpers.
- `smartdjango.code.Code` enumerates HTTP status codes.

## Public API

From `smartdjango.__init__`:

- `Validator`, `ValidatorErrors`
- `Params`
- `ListValidator`, `DictValidator`, `Key`
- `analyse`, `AnalyseErrors`
- `Choice`
- `Code`
- `Error`, `OK`
- `APIPacker`
