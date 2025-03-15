import gettext


class Translator:
    MODE_UPDATE = 0
    MODE_RELEASE = 1

    def __init__(self):
        self.langs = ['cn', 'en']
        self.localedir = './trans'
        self._translators = dict()
        self.current_lang = 'en'
        self.mode = self.MODE_UPDATE

    def load(self):
        self._translators = dict(zip(self.langs,
                                     gettext.translation('st', self.localedir, self.langs)))

    def set_lang(self, lang):
        if lang in self.langs:
            self.current_lang = lang
            return True
        return False

    def set_localedir(self, localedir):
        self.localedir = localedir


translator = Translator()
translator.load()
