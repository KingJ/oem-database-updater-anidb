class MockCollection(object):
    def __init__(self, source, target, storage=None):
        self.source = source
        self.target = target

        self.storage = storage


class MockFormat(object):
    def __init__(self, supports_binary):
        self.__supports_binary__ = supports_binary


class MockStorage(object):
    def __init__(self, fmt):
        self.format = fmt
