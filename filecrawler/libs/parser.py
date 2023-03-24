
class Parser(object):
    name = ''
    description = ''
    parser = ''
    qualname = ''
    _class = ''
    extensions = []
    mime_types = []

    def __init__(self, name, description, parser, qualname, class_name, extensions, mime_types):
        self.name = name
        self.description = description
        self.parser = parser
        self.qualname = qualname
        self._class = class_name
        self.extensions = [x.lower().strip(' .') for x in extensions]
        self.mime_types = [m.lower().strip(' .') for m in mime_types]

    def __str__(self):
        return self.name

    def create_instance(self):
        return self._class()

    def is_valid(self, extension: str, mime: str = None, mime_only: bool = False):

        if mime is None:
            mime = ''

        if extension is None:
            extension = ''

        mime = mime.strip(' .').lower()
        extension = extension.strip(' .').lower()

        if mime_only and (mime == '' or self.mime_types is None or len(self.mime_types) == 0):
            return False

        if (self.extensions is None or len(self.extensions) == 0) and \
                (self.mime_types is None or len(self.mime_types) == 0):
            return False

        if mime_only:
            return mime in self.mime_types

        return extension in self.extensions or mime in self.mime_types
