from typing import Dict, ClassVar


class ETemplate:
    """
    Error base Class
    """
    _id = 0  # 每个错误实例的唯一ID

    PH_NONE = 0
    PH_FORMAT = 1
    PH_S = 2

    def __init__(self, msg, ph=PH_NONE, hc=200):
        """
        错误类构造函数
        :param msg: explain
        :param ph: placeholder
        :param hc: http code
        """
        self.msg = msg
        self.ph = ph
        self.eid = ETemplate._id
        self.hc = hc  # http code
        self.class_ = None  # type: ClassVar

        ETemplate._id += 1

    def __call__(self, append_msg=None):
        return EInstance(self, append_msg or [])

    def __str__(self):
        return 'Error %s: %s' % (self.eid, self.msg)

    def dictor(self):
        from SmartDjango import Attribute
        return Attribute.dictor(self, 'msg', 'eid')


class EInstance:
    def __init__(self, e: ETemplate, append_msg=None):
        self.e = e
        self.append_msg = append_msg
        if (e.ph == ETemplate.PH_FORMAT or e.ph == ETemplate.PH_S) and isinstance(append_msg, str):
            self.append_msg = (append_msg,)

    def get_msg(self):
        if self.append_msg:
            if self.e.ph == ETemplate.PH_NONE:
                return self.e.msg + '，%s' % self.append_msg
            elif self.e.ph == ETemplate.PH_FORMAT:
                return self.e.msg.format(*self.append_msg)
            return self.e.msg % self.append_msg
        return self.e.msg

    def __str__(self):
        return 'EInstance of %s, %s' % (self.e, self.append_msg)


E = ETemplate
EI = EInstance


class ErrorJar:
    d = dict()  # type: Dict[str, ETemplate]
    d_i = dict()  # type: Dict[int, str]

    @classmethod
    def get(cls, k):
        return cls.d.get(k)

    @classmethod
    def get_i(cls, eid):
        if isinstance(eid, EInstance):
            eid = eid.e.eid
        elif isinstance(eid, ETemplate):
            eid = eid.eid
        return cls.d_i.get(eid)

    @classmethod
    def r_get(cls, eid):  # 兼容
        return cls.get_i(eid)

    @classmethod
    def all(cls):
        _dict = dict()
        for item in cls.d:
            _dict[item] = cls.d[item].dictor()
        return _dict

    @classmethod
    def pour(cls, class_):
        for k in class_.__dict__:  # type: str
            if not k.startswith('_'):
                e = getattr(class_, k)
                if isinstance(e, ETemplate):
                    if k in cls.d:
                        raise AttributeError(
                            '错误ID冲突，{0}在{1}中已存在'.format(k, cls.d[k].class_.__name__))
                    e.class_ = class_
                    cls.d[k] = e
                    cls.d_i[e.eid] = k
        return class_


@ErrorJar.pour
class BaseError:
    OK = E("没有错误", hc=200)
    FIELD_VALIDATOR = E("字段校验器错误", hc=500)
    FIELD_PROCESSOR = E("字段处理器错误", hc=500)
    FIELD_FORMAT = E("字段格式错误", hc=400)
    RET_FORMAT = E("函数返回格式错误", hc=500)
    MISS_PARAM = E("缺少参数{0}({1})", E.PH_FORMAT, hc=400)
    STRANGE = E("未知错误", hc=500)
