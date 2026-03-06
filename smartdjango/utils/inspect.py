import inspect


def get_function_arguments(func, *args, **kwargs):
    signature = inspect.signature(func)
    bound = signature.bind_partial(*args, **kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)
