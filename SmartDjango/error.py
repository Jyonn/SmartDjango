from .http_code import HttpCode as Hc
from smartify import E as BE, Attribute, BaseError, PError


class E(BE):
    def __init__(self, template: str, hc=Hc.OK, **kwargs):
        super(E, self).__init__(template, **kwargs)
        self.hc = hc

    def d(self):
        return Attribute.dictify(self, 'message->msg', 'eid', 'hc->http_code')


def error_update(e: BE, hc=Hc.OK):
    e.__class__ = E
    setattr(e, 'hc', hc)


error_update(BaseError.OK, hc=Hc.OK)
error_update(BaseError.ERROR_GENERATE, hc=Hc.InternalServerError)
error_update(PError.VALIDATOR_CRUSHED, hc=Hc.InternalServerError)
error_update(PError.PROCESSOR_CRUSHED, hc=Hc.InternalServerError)
error_update(PError.REQUIRE_DICT, hc=Hc.Forbidden)
error_update(PError.REQUIRE_LIST, hc=Hc.Forbidden)
error_update(PError.NULL_NOT_ALLOW, hc=Hc.Forbidden)
error_update(PError.PATTERN_NOT_MATCH, hc=Hc.Forbidden)
