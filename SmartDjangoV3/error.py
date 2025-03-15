from .http_code import HttpCode as Hc
from smartify import E as BE, Attribute, BaseError, PError


class E(BE):
    def __init__(self, template: str, hc=Hc.OK):
        super(E, self).__init__(template)
        self.hc = hc

    def d(self):
        dict_ = super(E, self).d()
        dict_.update(Attribute.dictify(self, 'hc->http_code', 'eid->code'))
        del dict_['eid']
        return dict_

    def d_debug(self):
        return super(E, self).d_debug()


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
