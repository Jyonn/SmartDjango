class EInstance:
    def __init__(self, e, append_msg=None):
        self.e = e
        self.append_msg = append_msg


class E:
    """
    错误类，基类
    """
    _id = 0  # 每个错误实例的唯一ID

    def __init__(self, msg, release=None):
        """
        错误类构造函数
        :param msg: 错误的中文解释
        :param release: 此错误在发行环境下跳转为其他错误
        """
        self.msg = msg
        self.release = release
        self.eid = E._id

        E._id += 1

    def __call__(self, append_msg):
        return EInstance(self, append_msg)


class BaseError:
    OK = E("没有错误")
    FIELD_VALIDATOR = E("字段校验器错误")
    FIELD_PROCESSOR = E("字段处理器错误")
    FIELD_FORMAT = E("字段格式错误")
    RET_FORMAT = E("函数返回格式错误")


class ErrorDict:
    __d = dict()
    __reversed_d = dict()

    @staticmethod
    def update(error_class):
        for k in error_class.__dict__:
            e = getattr(error_class, k)
            if isinstance(e, E):
                ErrorDict.__d[k] = e
                ErrorDict.__reversed_d[e.eid] = k

    @staticmethod
    def get(k):
        return getattr(ErrorDict.__d, k)

    @staticmethod
    def r_get(eid):
        return getattr(ErrorDict.__reversed_d, eid)


ErrorDict.update(BaseError)
