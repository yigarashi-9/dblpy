class Error(Exception):
    pass


class HttpGetError(Error):
    def __init__(self, url: str) -> None:
        self.url = url


class NoFileExistsError(Error):
    def __init__(self, path: str) -> None:
        self.path = path
