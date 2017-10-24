import argparse
import logging
import os
import sys
from typing import cast, List, Optional
import urllib.parse

from lxml import html  # type: ignore
import pyperclip  # type: ignore
import requests

from .exceptions import *
from .query import Query


def download_html(url: str, logger: logging.Logger) -> str:
    try:
        logger.info("Sending a request: " + url)
        return requests.get(url).text
    except:
        raise HttpGetError(url)


def get_bib_page_url(query: Query, logger: logging.Logger) -> Optional[str]:
    url = "http://dblp.uni-trier.de/search?q=" + urllib.parse.quote(str(query))
    root = html.fromstring(download_html(url, logger))
    node_of_entries = root.xpath("//*[@class=\"publ\"]/ul/li[2]/div[1]/a")

    if len(node_of_entries) == 0:
        return None

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


def _main() -> int:
    logger: logging.Logger = logging.getLogger(__name__)
    handler: logging.Handler = logging.StreamHandler(stream=sys.stdout)
    formatter: logging.Formatter = logging.Formatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    parser: argparse.ArgumentParser = build_parser()
    exit_status : int = 0

    try:
        args: argparse.Namespace = parser.parse_args()

        if args.info:
            logger.setLevel(logging.INFO)
            handler.setLevel(logging.INFO)

        query: Query = Query(args, logger)

        if query.title is None:
            print("No title info: " + args.query)
            return exit_status

        logger.info("Building a query: " + str(query))
        bib_page_url: Optional[str] = get_bib_page_url(query, logger)

        if bib_page_url is None:
            print("No matches: " + str(query))
            return exit_status

        bibtext: str = get_bib_text(bib_page_url, logger)
        pyperclip.copy(bibtext)
        print("Copied to the clipboard:")
        print(bibtext)
    except HttpGetError as err:
        sys.stderr.write("Failed to access: " + err.url)
        exit_status = 1
    except NoFileExistsError as err:
        sys.stderr.write("No such file: " + err.path)
        exit_status = 1

    return exit_status
