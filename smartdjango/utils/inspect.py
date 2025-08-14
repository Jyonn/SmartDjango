import inspect


def get_function_arguments(func, *args, **kwargs):
    datadict = dict()
    parameters = inspect.signature(func).parameters
    for parameter in parameters:
        param = parameters[parameter]
        datadict[parameter] = param.default
    names = list(parameters.keys()) + list(kwargs.keys())

    datadict = dict(zip(names, args))
    datadict.update(kwargs)
    return datadict
