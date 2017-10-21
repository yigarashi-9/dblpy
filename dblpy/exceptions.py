class Error(Exception):
    pass


class HttpGetError(Error):
    def __init__(self, url):
        self.url = url


class FileError(Error):
    def __init__(self, path):
        self.path = path


class NoFileExistsError(FileError):
    pass


class NoTitleExistsError(FileError):
    pass


class NoMatchError(Error):
    def __init__(self, query):
        self.query = query
