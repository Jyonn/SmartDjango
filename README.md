# SmartDjango

## Introduction

**SmartDjango** is a high-level packed developing tools for Django.

It provides the following features:

- Smart middleware for auto packing json-format response
- Smart fields for restricting value, such as min_length of a CharField,
  or max_value/min_value of an IntegerField
- Smart param for value validating and processing, which can be
  generated by a field quickly.
- Smart analysis tool for analysing parameters of any method's input,
  especially the Request object. So the parameters can be
  formatted/detected before methods running.
- Smart error for identifying, recording and response.
- Smart pager for partly response objects the model filtered.

## Installation

```
pip install SmartDjango
```

The latest version is `3.5.1`, building on 29th Oct, 2019. It requires
`Django >= 2.2.5`.

## Hints

### Language Limited

Current Version is based on Chinese, as you can see in some readable
errors.

`error.py`
```python
class BaseError:
    OK = E("没有错误", hc=200)
    FIELD_VALIDATOR = E("字段校验器错误", hc=500)
    FIELD_PROCESSOR = E("字段处理器错误", hc=500)
    FIELD_FORMAT = E("字段格式错误", hc=400)
    RET_FORMAT = E("函数返回格式错误", hc=500)
    MISS_PARAM = E("缺少参数{0}({1})", E.PH_FORMAT, hc=400)
    STRANGE = E("未知错误", hc=500)
```

We will later support more languages.

### Django familiarity

You need to be familiar with Django development, including models, views
as well as basic server development.

## Tutorial

**We assume you have setup Django environment, with database correctly
configured.**

### No hundreds times' `return JsonResponse`!

JSON is a popular format for data transferring. The following code is
usually used to pack dict data to HTTPResponse object:

```python
def handler(r):
    data = get_data()  # type: dict
    return HttpResponse(
                json.dumps(data, ensure_ascii=False),  # for showing Chinese characters
                content_type="application/json; encoding=utf-8",
            )
```

or an easier way:

```python
def handler(r):
    data = get_data()  # type: dict
    return JsonResponse(data)
```

Now it's the easiest way:

```python
def handler(r):
    data = get_data()  # type: dict
    return data
```

You may have dozens of handlers, but you don't need to write dozens of
`JsonResponse`. What's all you need is to append a single line in
`MIDDLEWARES` in setting file like this:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    ...
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'SmartDjango.middleware.HttpPackMiddleware',
]
```

The middleware will directly pass `HttpResponse` object, handle errors
which error module creates and importantly pack `dict` data.

### Model value detect

It's a common requirement to limit the length of username to 3 to 16,
and limit its characters to `a` to `z`. As `CharField` only has
`max_length` attribute, what we usually do is:

```python
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=16)
    password = models.CharField(max_length=16)
    ...
    
    @classmethod
    def new(cls, username, password):
        if not cls.check_username_is_alpha(username):
            raise Exception
        if not cls.check_username_max_min_length(username):
            raise Exception
        if not cls.check_password_max_min_length(password):
            raise Exception
        user = cls(username=username, password=password)
        user.save()
        return user
```
Now we have a more elegant and magical solution:

```python
from SmartDjango import models, E, Excp

@E.register
class UserError:
    USERNAME_ALPHA = E(
        "Username should only be consist of alphas.", 
        hc=403,  # http code
    )

class User(models.Model):
    username = models.CharField(max_length=16, min_length=3)
    password = models.CharField(max_length=16, min_length=6)
    ...
    
    @staticmethod
    def _valid_username(username: str):
        for c in username:
            if not 'a' < c.lower() < 'z':
                raise UserError.USERNAME_ALPHA  # or raise
                
    @classmethod
    def new(cls, username, password):
        cls.validator(locals())
        
        user = cls(username=username, password=password)
        user.save()
        return user
```

We firstly create an error class, for storing all errors would faced in
user model. Here `USERNAME_ALPHA` is the identifier of this error, with
description and http code.

This error is used in `User._valid_username` method. SmartDjango will
detect if there is a attribute-level validator named `_valid_ATTRIBUTE`
in this class when calling `cls.validator`.

If the validator, called in `new` method, returns/raises an error, `new`
method will bubble this error to upper method. As it arrives in
`middleware`, it will be handled and shown as json response.

Another thing is max length and min length. `cls.validator` will also
detects values if fitting the configuration of fields.

### Avoid bad parameters before entering the handler!

In fact, if the username posted is not valid, we could stop it at the
beginning.

Here's the code we usually write in `views.py` to get register
information, create a user and return something.

```python
from django.views import View
from User.models import User

import json

class UserView(View):
    @staticmethod
    def post(r):
        data = json.loads(r)
        username = data['username']
        password = data['password']
        user = User.new(username, password)  # assuming we adopt the code above
        
        return dict(id=user.pk, username=user.username)  # middleware will handle it!
```

Try this easier way:

`models.py` 
```python
from SmartDjango import models, E, Excp, P

@E.register
...

class User(models.Model):
    def _readable_id(self):
        return self.pk
        
    def d(self):
        return self.dictor('username', 'id')
...

class UserP:
    username, password = User.get_params('username', 'password')
```

`views.py`
```python
from django.views import View
from SmartDjango import Analyse
from User.models import User, UserP

class UserView(View):
    @staticmethod
    @Analyse.r(b=[UserP.username, UserP.password])  # 'b' means body 
    def post(r):
        username = r.d.username
        password = r.d.password
        user = User.new(username, password)  # or User.new(**r.d.dict())
                                             # or User.new(**r.d.dict('username', 'password'))
        return user.d()
```

As you can see, we support many new features.

#### Analyse parameters which can be custom or generated magically by model fields   

Firstly, `UserP` means **Parameters created by User**. `UserP.username`
and `UserP.passowrd` succeed features like max/min length and custom
validator of username and password field.

In `views.py`, we use `Analyse.r` to analyse parameters in `r`(request).
`b` stands for `body`, `q` stands for `query` and `a` stands for
arguments. For example, the API: 

```
POST /api/zoo/insect/search?count=5&last=0

{
    "name": "fly",
    "color": null
}
```

with the url pattern: `path('/api/zoo/<str: kind>/search',
some_handler)`, the some handler should be written as:

```python
from SmartDjango import P, Analyse

@Analyse.r(
    b=[P('name', read_name='name of insert'), P('color').set_null()],
    q=[P('count').process(int).process(lambda x: min(1, x)), P('last').process(int)],
    a=[P('kind')]
)
def some_handler(r):
    pass
```

OK now we back to the `UserView`. The `Analyse` decorator will check
these two parameters if valid. Only if they passed the analysis, they
will be stored in `r.d` object. It's obviously more convenient to use
**dot**-`username` than **quote**-`username`-**quote**.

Also the `dict` method is provided to fetch all/specific parameters.

#### Simple way to get information of a model instance

The next magic is `models.dictor`.

It would be very boring to write something like this:

```python
def d(self):
    return dict(
        id=self.pk,
        birthday=self.birthday.strftime('%Y-%m-%d'),  # datetime -> str
        username=self.username,
        description=self.description,
        male=self.male,
        school=self.school,
        ...
    )
```

Now `dictor` is born, and the bore is gone.

`dictor` will detect firstly `_readable_ATTRIBUTE` for each attributes.
If detected, it will record dict(attribute=self._readable_ATTRIBUTE()),
or else it will find if the model has this attribute.

What we make easy is 2 `school`s at beginning but now only once. It can
be simplified like this:

```python
def _readable_id(self):
    return self.pk
    
def _readable_birthday(self, timestamp=False):
    if timestamp:
        return self.birthday.timestamp()
    else:
        return self.birthday.strftime('%Y-%m-%d')
        
def d(self):
    return self.dictor('id', ('birthday', True), 'username', 'description', 'male', 'school', ...) 
```

### More custom for P

#### yield_name and processor

Assuming now you want to get some user's information with its user_id.

Former way:

```python
@Analyse.r(q=['user_id'])
def handler(r):
    user_id = r.d.user_id
    user = User.get(user_id)
    return user.d()
```

Magic way:

```python
@Analyse.r(q=[P('user_id', yield_name='user').process(User.get)])
def handler(r):
    return r.d.user.d()
```

Or use `Processor`:

```python
@Analyse.r(q=[P('user_id').process(P.Processor(User.get, yield_name='user'))])
def handler(r):
    return r.d.user.d()
```

The priority of `yield_name` in P is lower than it in `Processor`.

#### validator

Validator is a simpler limitation compared with Processor. It's a
Processor, but the simple version. It will be stored with other
processors.

Validator only returns error or None. If None, the value doesn't change.
Processor will change value and is able to change parameter's name
(yield_name).

If some parameters have more than one validators or processors, the
order of those makes a significant effect. Take a timestamp string as an
example, if we want to extract datetime information of the string
`"1572451778"`, we firstly need to transfer it as the integer
`1572451778`, then use datetime methods to process this integer to a
datetime object. The order of the processors is based on the order the
processor defined, unless you use `begin` argument. The right way to
handle the problem above should be one of the following codes.

```python
P('time').processor(int).processor(datetime.datetime.fromtimestamp)
```

or

```python
P('time').processor(datetime.datetime.fromtimestamp).processor(int, begin=True)
```

You might think the second method is stupid in some kind, but it's an
usual phenomenon. Think about it:

`models.py`
```python
class SomeModel(models.Model):
    time = models.DatetimeField(...)
    
class SomeModelP:
    time = SomeModel.get_param('time')
    time.processor(datetime.datetime.fromtimestamp, begin=True).processor(int, begin=True)
```

`SomeModelP.time` is created as a `P`, and its build-in validator will
check if the value is instance of `Datetime`. As mentioned above,
validator is stored with other processors (in one processor list), we
need to process the string-format timestamp to datetime type. So what we
always do is add two processors.

#### default and null

Sometimes parameter may have default value or can be null. If some
parameter `set_null` and it posted as null, it will only change it's
`yield_name` and the value will stay `null`. You can use
`set_null(null=False)` to change its state.

If some parameter would have default value, `set_default` will show its
function. When a `P` doesn't set null but set default, it will get a
default value. For example, `P('count').set_default(10,
through_processor=True)`. If `through_processor` is `False`(default),
the value will stay at default value(10); but when this switch is on, it
will go through all validators and processors.

#### rename and clone

`P` can be generated by `models.get_params`. If we want to custom some
`P` based on it, we can use `clone` method to get a new `P` with all
features.

Rename would be a huge demand, to change parameter's name, read name and
yield name.

### One more thing

#### better searching

Django provides convenient `filter` method to select items we want based
on fields we limited. But when we do some search things, like get
students whose name contains `Jyonn`, we would code like this:

```python
SomeClass.objects.filter(name__contains='Jyonn')
``` 

Search takes the secondary place cause `name='Jyonn'` means the name is
exactly `Jyonn`. Now we want to take `search` as important as `filter`.
And the dream has come true:

```python
SomeClass.objects.search(name='Jyonn')
```

We use `name__full='Jyonn'` in `search` to replace `name='Jyonn'` in
`filter`. We also support custom design. For example, we want to get all
apps with user number above 500(some digit) and created time in 1
year(some day). Try this:

`models.py`
```python
class App(models.Model):
    user_num = models.IntegerField(...)
    create_time = models.DatetimeField(...)
    
    def _search_user_num(self, v):
        return dict(user_num__gte=v)
        
    def _search_create_time(self, v):
        return dict(create_time__gte=v)
        
class AppP:
    user_num, create_time = App.get_params('user_num', 'create_time')
    create_time.processor(datetime.datetime.fromtimestamp, begin=True).processor(int, begin=True)
```

`views.py`
```python
class SearchView(View):
    @staticmethod
    @Analyse.r(q=[AppP.user_num, AppP.create_time])
    def get(r):
        user_num = r.d.user_num
        create_time = r.d.create_time
        objects = App.search(user_num=user_num, create_time=create_time)
        # or
        objects = App.search(**r.d.dict()) 
        ...
```

We pack `_gte` or some other things into the model, so the code in views
could be quite simple and elegant.

You will find more colorful usage. Try SmartDjango!