# SmartDjango Handbook For Codex

This document is a source-grounded guide to the `smartdjango` library in this repository. It is intended for Codex instances working in downstream Django projects that depend on this package.

Status: updated after bug-fix pass on 2026-03-06.

## 1. What This Library Is

`smartdjango` is a compact utility library focused on API-oriented Django projects:

- A unified `Error` type with identifiers and JSON payload shaping.
- Middleware (`APIPacker`) that wraps non-`HttpResponse` return values into a common API envelope.
- Declarative input validation (`Validator`, `DictValidator`, `ListValidator`, `Params`).
- Decorators to validate request JSON/query/path arguments (`smartdjango.analyse`).
- Small ORM helpers (`QuerySet.map`, `Manager.map`, abstract `Model` base class).
- A simple paginator abstraction for offset and cursor-ish patterns.

The package is intentionally small; most behavior is concentrated in a few modules.

## 2. Repo Snapshot

Top-level package contents:

- `smartdjango/error.py`: core `Error` object + global registry.
- `smartdjango/code.py`: HTTP-like status constants.
- `smartdjango/middleware.py`: response envelope middleware.
- `smartdjango/analyse.py`: request/function decorators and data attachment.
- `smartdjango/validation/*`: validators and model-field-to-validator generation.
- `smartdjango/models/*`: manager/queryset/model conveniences.
- `smartdjango/paginator.py`: page container and paginator logic.
- `smartdjango/utils/io.py`, `smartdjango/utils/inspect.py`: utility helpers.
- `smartdjango/choice.py`: class constant -> Django choices converter.
- `smartdjango/__init__.py`: public exports.

## 3. Public API Surface

`smartdjango/__init__.py` exports:

- `Validator`, `ValidatorErrors`
- `Params`
- `ListValidator`, `DictValidator`, `Key`
- `AnalyseErrors`, `analyse`
- `Choice`
- `Code`
- `Error`, `OK`
- `APIPacker`

For downstream code, treat only these as stable entry points unless you intentionally depend on internals.

## 4. Runtime Data Flow

Typical API request flow when using this library:

1. Django route dispatches to a view.
2. `@analyse.*` decorator validates one input source and writes cleaned data to:
   - `request.json`, `request.query`, or `request.argument`
   - merged aggregate `request.data`
3. View returns either:
   - a `django.http.HttpResponse`, or
   - plain Python data, or
   - an `Error`
4. `APIPacker` converts non-`HttpResponse` outputs into:
   - status from `Error.code` (or 200 via `OK`)
   - JSON body with keys `message`, `code`, `details`, `user_message`, `identifier`, `body`

Error-first behavior is central: validation failures raise `Error` subclasses/instances that middleware serializes consistently.

## 5. Core Module Details

### 5.1 `error.py`

Key behavior:

- `Error` extends `Exception`.
- `Error.register` enforces class naming suffix `*Errors` and auto-assigns identifiers:
  - class name prefix (without `Errors`) uppercased
  - format: `PREFIX@CONSTANT_NAME`
- `__call__` clones an error template and allows:
  - message/user_message formatting with kwargs
  - appending `details`
- global registry `Error.all()` stores all identifiers.

Practical meaning:

- You define reusable error templates as constants.
- At raise-time, call template to inject details/kwargs.
- Identifier uniqueness is enforced globally.

### 5.2 `code.py`

- `Code` is a namespace class of integer status codes.
- Used throughout errors and API responses.
- Includes standard HTTP statuses and some uncommon ones.

### 5.3 `middleware.py` (`APIPacker`)

Contract:

- Pass-through if view returns `HttpResponse`.
- If return value is `Error`:
  - serialized as `error.json()`
  - HTTP status = `error.code`
  - `body = None`
- Else:
  - wraps value as `body`
  - uses `OK` envelope and status 200

`process_exception` supports converting thrown `Error` into packed JSON.

### 5.4 Validation stack (`validation/*`)

#### `Validator`

Pipeline in `clean(value)`:

1. Handle unset sentinel:
   - if no default -> `ValidatorErrors.NO_DEFAULT`
   - else default value
2. Handle `None`:
   - if `allow_null` false -> `NULL_NOT_ALLOW`
3. Apply `.to(...)` converters in order.
4. Apply validators from `.bool(...)` / `.exception(...)` in order.

Metadata:

- Optional key descriptor (`Key`) includes:
  - input name (`name`)
  - human-readable name (`verbose_name`)
  - output field name (`final_name`)
- Errors are augmented with target-key detail when key is present.

Factory:

- `Validator.from_field(model_field, ...)` derives rules from Django field metadata:
  - `null`, `default`, `choices`
  - basic type checks for common field classes.

#### `DictValidator`

- Stores keyed field validators.
- `fields(...)` builds the schema.
- `restrict_keys()` rejects unknown input keys.
- `clean(dict)` returns a new dict keyed by each field validator's `final_name`.

Important: this is the backbone of all `analyse.*` decorators.

#### `ListValidator`

- `element(v)` applies one validator to every list element.
- `elements(v1, v2, ...)` is intended for fixed-position validation.
- `clean` enforces input is `list`.

#### `Params` metaclass

Purpose:

- Lazy validator generation from Django model fields.

Pattern:

```python
class UserParams(metaclass=Params):
    model_class = User

UserParams.username  # returns cached Validator.from_field(...)
```

This reduces duplication between model schema and input validation schema.

#### `Key`

- Normalizes key identity and output renaming.
- Dict validation logic compares incoming keys by `Key.__eq__` against strings.

### 5.5 `analyse.py`

Decorators:

- `analyse.json(...)`: validates JSON-decoded `request.body`.
- `analyse.query(...)`: validates `request.GET.dict()`.
- `analyse.argument(...)`: validates view kwargs.
- `analyse.request(bool_func, message)`: validates request object itself.
- `analyse.function(...)`: validates plain-function arguments after signature binding/default filling.

Shared internals:

- `get_request(*args)` scans positional args for `HttpRequest`.
- `update_to_data` merges validated payloads into `request.data`.
- each decorator uses a `DictValidator` schema built from provided validators.

### 5.6 `models/*`

- `QuerySet.map(func, ...)` maps objects to a Python list.
- `Manager.get_queryset()` returns the custom `QuerySet`.
- `Manager.map(...)` convenience pass-through.
- Abstract `Model` combines Django `Model` with `diq.Dictify` and default manager override.

This module is mostly ergonomic sugar for API serialization pipelines.

### 5.7 `paginator.py`

Two paging modes:

- Offset mode: `get_page(page=int)` where `next` is next page number or `False`.
- Cursor-like mode:
  - call `filter(field__lt=value)` or `filter(field__gt=value)` first
  - call `get_page(page=None)`
  - `next` is field value from last object (or `False`)

`Page.dict(object_map, next_map=None)` serializes the page payload.

### 5.8 `utils/*`

- `io.py`:
  - JSON load/save, JSONL load, text file load/save, pickle load/save.
- `inspect.py`:
  - helper that binds args/kwargs to function signature and applies defaults.

### 5.9 `choice.py`

- `Choice.to_choices()` converts class attributes to Django choice tuples `[(v, v), ...]` excluding private attrs.

## 6. Downstream Integration Guidance

Recommended minimum integration for Django API projects:

1. Add middleware:
   - `smartdjango.middleware.APIPacker`
2. Define domain-specific error registries:
   - `@Error.register class UserErrors: ...`
3. Validate all inbound request surfaces with `analyse.json/query/argument`.
4. Keep view return contract simple:
   - return `HttpResponse` when fully custom
   - otherwise return plain data or `Error`
5. Optionally use `Params` + model metadata for CRUD endpoint validators.

Reference response envelope:

```json
{
  "message": "OK or error template message",
  "code": 200,
  "details": [],
  "user_message": "safe message",
  "identifier": "OK or PREFIX@ERROR",
  "body": {}
}
```

## 7. Coding Conventions For Codex In Dependent Repos

When writing code against this library:

- Prefer imported symbols from `smartdjango` package root (`from smartdjango import ...`).
- Treat `Error` objects as reusable templates:
  - define once, clone with `Errors.SOMETHING(details=..., key=...)`.
- Make validator schemas explicit and stable; use `restrict_keys()` for strict APIs.
- Use `final_name` to decouple external request names from internal field names.
- Keep `request.data` as the unified source after multiple `analyse.*` decorators.

## 8. Current Design Notes (Post-Fix)

The previous high-impact bugs were fixed (argument analysis, list fixed-schema validation, string rendering, validator copy behavior, packaging metadata, paginator count refresh).

Current non-bug constraints and intentional behavior:

1. `Validator.from_field` intentionally skips `BaseValidator` subclasses.
   - `smartdjango/validation/validator.py` only adds validators when `not isinstance(field_validator, BaseValidator)`.
   - this is a deliberate design choice in this repo.

2. `analyse.function` calls the wrapped function as keyword arguments (`func(**arguments)`).
   - avoid positional-only function signatures when using this decorator.

3. `Paginator.filter(...)` allows exactly one comparator (`field__lt` or `field__gt`) at a time by design.

No unresolved runtime bugs are currently tracked in this handbook.

## 9. Suggested Roadmap (Next Improvements)

Priority order:

1. Add regression tests for the fixed behaviors:
   - `analyse.function` argument binding/defaults.
   - `ListValidator.elements(...)` fixed-position validation.
   - `Validator.copy()` with/without keys.
   - paginator count updates after `filter`.
2. Decide whether positional-only support is needed for `analyse.function`.
3. Add test suite covering:
   - middleware packing
   - validator defaults/null/type/rename
   - decorators + request data merging
   - paginator offset/cursor flows and count semantics

## 10. Quick Reference Recipes

### Strict JSON payload validation

```python
from smartdjango import analyse, Validator

CreateUserV = (
    Validator("username")
    .bool(lambda v: isinstance(v, str), message="username must be string")
)

@analyse.json(CreateUserV, restrict_keys=True)
def create_user(request):
    username = request.json.username
    return {"username": username}
```

### Error template and instance

```python
from smartdjango import Error, Code

@Error.register
class UserErrors:
    NOT_FOUND = Error("User {uid} not found", code=Code.NotFound)

def get_user(uid):
    raise UserErrors.NOT_FOUND(uid=uid, details=f"id={uid}")
```

### Model-derived validator access

```python
from smartdjango import Params

class UserParams(metaclass=Params):
    model_class = User

username_validator = UserParams.username
```

## 11. Bottom Line For Other Codex Agents

- Use this library primarily as an API contract normalizer plus validator toolkit.
- The most reliable pieces today are: `Error`, `APIPacker`, `Validator`, `DictValidator`, `analyse.json/query/argument/function`.
- Use `Validator.from_field` with the understanding that Django `BaseValidator` subclasses are intentionally excluded.
- If you are generating code in downstream repos, prefer explicit validators and strict keys for predictable API behavior.
