import argparse
import logging
import os
from typing import BinaryIO, Optional
import urllib.parse

from PyPDF2 import PdfFileReader  # type: ignore

from .exceptions import NoFileExistsError


class DblpQuery:
    def __init__(self, args: argparse.Namespace,
                 logger: logging.Logger) -> None:
        if args.file:
            self.title = self.extract_title_from_pdf(args.query, logger)
        else:
            self.title = args.query

        self.author = args.author  # type: List[str]
        self.year = args.year  # type: int
        self.venue = args.venue  # type: str
        self.conf = args.conf  # type: bool
        self.journal = args.journal  # type: bool

    def extract_title_from_pdf(self, path: str,
                               logger: logging.Logger) -> Optional[str]:
        if not os.path.isfile(path):
            raise NoFileExistsError(path)

        f: BinaryIO = open(path, 'rb')
        logger.info("Parsing pdf: " + path)
        info = PdfFileReader(f, strict=False).getDocumentInfo()

        if info is None or info.title is None or info.title == "":
            return None

        logger.info("Extracted title: " + info.title)
        return info.title

    @property
    def url(self) -> str:
        return ("http://dblp.org/search/publ/api?q="
                + urllib.parse.quote(str(self)))

    def __str__(self) -> str:
        if self.title is None:
            return ""

        s: str = self.title

        if self.author:
            for author in self.author:
                s += " " + author

        s += f" year:{str(self.year)}:" if self.year else ""
        s += f" venue:{self.venue}:" if self.venue else ""

        if self.conf:
            s += " type:Conference_and_Workshop_Papers:"

        if self.journal:
            s += " type:Journal_Articles:"

        return s
