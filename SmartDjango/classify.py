class Classify:
    def dict(self, *args):
        if args:
            dict_ = dict()
            for k in args:
                dict_[k] = self._dict.get(k)
            return dict_
        return self._dict

    def __init__(self, d):
        if not isinstance(d, dict):
            return
        object.__setattr__(self, '_dict', d)

    def __getattr__(self, item):
        return self._dict.get(item)

    def __setattr__(self, key, value):
        self._dict[key] = value
