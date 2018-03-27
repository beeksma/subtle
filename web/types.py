import os


class SubtitleQuery(object):
    Results = None
    Video = None

    def __init__(self, video):
        self.Video = video


class Navigator(object):
    __path = None
    __root = None
    dirs = None
    files = None

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, value):
        self.__path = value

    @property
    def parent(self):
        return os.path.abspath(os.path.join(self.path, os.pardir))

    @property
    def root(self):
        return self.__root

    @root.setter
    def root(self, value):
        self.__root = value

    def __init__(self):
        self.root = os.path.abspath(os.sep)
        self.path = self.root
