import os


class SubtitleQuery(object):
    Results = None
    Video = None

    def __init__(self, video):
        self.Video = video


class Navigator(object):
    __path = None

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
        return os.path.abspath(os.sep)

    def __init__(self):
        self.path = self.root
