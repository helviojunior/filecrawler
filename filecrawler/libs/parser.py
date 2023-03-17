
class Parser(object):
    name = ''
    description = ''
    parser = ''
    qualname = ''
    _class = ''
    extensions = []

    def __init__(self, name, description, parser, qualname, class_name, extensions):
        self.name = name
        self.description = description
        self.parser = parser
        self.qualname = qualname
        self._class = class_name
        self.extensions = extensions
        pass

    def create_instance(self):
        return self._class()

    def is_valid(self, extension: str):
        if self.extensions is None or len(self.extensions) == 0:
            return False

        return extension.strip(' .').lower() in self.extensions
