from .http_code import HttpCode as Hc
from smartify import E as BE, Attribute


class E(BE):
    def __init__(self, message: str, hc=Hc.OK):
        super(E, self).__init__(message)
        self.hc = hc

    def d(self):
        return Attribute.dictify(self, 'message->msg', 'eid', 'hc->http_code')
