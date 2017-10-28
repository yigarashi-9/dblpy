class Error(Exception):
    pass


class DownloadError(Error):
    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason

    def __str__(self) -> str:
        return f"{self.reason}: {self.url}"


class NoFileExistsError(Error):
    def __init__(self, path: str) -> None:
        self.path = path
