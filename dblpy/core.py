import argparse
import logging
import os
import sys
from typing import cast, BinaryIO, List
import urllib.parse

from lxml import html  # type: ignore
from PyPDF2 import PdfFileReader  # type: ignore
import pyperclip  # type: ignore
import requests

from .exceptions import *


class Query:
    def __init__(self, args: argparse.Namespace, logger: logging.Logger) -> None:
        if args.file:
            self.title = extract_title_from_pdf(args.query, logger)  # type: str
        else:
            self.title = args.query

        self.author = args.author  # type: List[str]
        self.year = args.year  # type: int
        self.venue = args.venue  # type: str
        self.conf = args.conf  # type: bool
        self.journal = args.journal  # type: bool


    def __str__(self) -> str:
        s = self.title

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


def extract_title_from_pdf(path: str, logger: logging.Logger) -> str:
    if not os.path.isfile(path):
        raise NoFileExistsError(path)

    f: BinaryIO  = open(path, 'rb')
    logger.info("Parsing pdf: " + path)
    info = PdfFileReader(f, strict=False).getDocumentInfo()

    if info is None or info.title is None or info.title == "":
        raise NoTitleExistsError(path)

    logger.info("Extracted title: " + info.title)
    return info.title


def download_html(url: str, logger: logging.Logger) -> str:
    try:
        logger.info("Sending a request: " + url)
        return requests.get(url).text
    except:
        raise HttpGetError(url)


def get_bib_page_url(query: Query, logger: logging.Logger) -> str:
    url = "http://dblp.uni-trier.de/search?q=" + urllib.parse.quote(str(query))
    root = html.fromstring(download_html(url, logger))
    node_of_entries = root.xpath("//*[@class=\"publ\"]/ul/li[2]/div[1]/a")

    if len(node_of_entries) == 0:
        raise NoMatchError(query)

    return node_of_entries[0].attrib["href"]


def get_bib_text(url: str, logger: logging.Logger) -> str:
    root = html.fromstring(download_html(url, logger))
    return root.xpath("//*[@id=\"bibtex-section\"]/pre[1]")[0].text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Copy bibtex entry from DBLP")
    parser.add_argument("-f", "--file", action="store_true",
                        help="interpret query as file path")
    parser.add_argument("-i", "--info", action="store_true",
                        help="display verbose information")
    parser.add_argument("query", type=str)
    refine_group = parser.add_argument_group(title="Refine list")
    refine_group.add_argument("-a", "--author", action="append")
    refine_group.add_argument("-y", "--year", type=int)
    refine_group.add_argument("-v", "--venue", type=str)
    type_group = refine_group.add_mutually_exclusive_group()
    type_group.add_argument("-c", "--conf", action="store_true",
                            help="Conference and Workshop Papers")
    type_group.add_argument("-j", "--journal", action="store_true",
                            help="Journal Articles")
    return parser


def main() -> int:
    logger: logging.Logger = logging.getLogger(__name__)
    handler: logging.Handler = logging.StreamHandler(stream=sys.stdout)
    formatter: logging.Formatter = logging.Formatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    parser: argparse.ArgumentParser = build_parser()
    exit_status: int = 1

    try:
        args: argparse.Namespace = parser.parse_args()

        if args.info:
            logger.setLevel(logging.INFO)
            handler.setLevel(logging.INFO)

        query: Query = Query(args, logger)
        logger.info("Building a query: " + str(query))
        bib_page_url: str = get_bib_page_url(query, logger)
        bibtext: str = get_bib_text(bib_page_url, logger)
        pyperclip.copy(bibtext)
        print("Copied to the clipboard:")
        print(bibtext)
        exit_status = 0
    except HttpGetError as err:
        sys.stderr.write("Failed to access: " + err.url)
    except NoFileExistsError as err:
        sys.stderr.write("No such file: " + err.path)
    except NoTitleExistsError as err:
        sys.stderr.write("No title info: " + err.path)
    except NoMatchError as err:
        sys.stderr.write("No matches: " + str(err.query))

    return exit_status
