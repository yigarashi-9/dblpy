import argparse
import logging
import sys
from typing import List

from lxml import etree
from lxml import html  # type: ignore
import requests

from .exceptions import DownloadError, NoFileExistsError
from .query import DblpQuery


def download(url: str, logger: logging.Logger) -> str:
    try:
        logger.info("Sending a request: " + url)
        r = requests.get(url)
        r.raise_for_status()
        return r.text
    except requests.exceptions.HTTPError as e:
        raise DownloadError(url,
                            f"{e.response.status_code} {e.response.reason}")
    except requests.exceptions.ConnectionError:
        raise DownloadError(url, "Connection Error")
    except requests.exceptions.Timeout:
        raise DownloadError(url, "Timeout")
    except requests.exceptions.TooManyRedirects:
        raise DownloadError(url, "Too many redirects")


def download_article_entries(url: str,
                             logger: logging.Logger) -> List[etree._Element]:
    root: etree._Element = etree.fromstring(
        download(url, logger).encode('utf-8'))
    return root.xpath("/result/hits/hit")


def download_bib_text(url: str, logger: logging.Logger) -> str:
    root = html.fromstring(download(url, logger))
    return root.xpath("//*[@id=\"bibtex-section\"]/pre[1]")[0].text


def format_article_entry(entry: etree._Element) -> str:
    title = entry.xpath("info/title")[0].text
    venue = entry.xpath("info/venue")[0].text
    return title + " in " + venue


def get_bib_page_url(entry: etree._Element) -> str:
    return entry.xpath("info/url")[0].text.replace("rec", "rec/bibtex", 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Copy bibtex entry from DBLP")
    parser.add_argument("-f", "--file", action="store_true",
                        help="interpret query as file path")
    parser.add_argument("-i", "--info", action="store_true",
                        help="display verbose information")
    parser.add_argument("-n", "--number", type=int, default=5,
                        help="limit of number of results")
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
    formatter: logging.Formatter = logging.Formatter()  # flake8: noqa
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    parser: argparse.ArgumentParser = build_parser()
    args: argparse.Namespace = parser.parse_args()

    if args.info:
        logger.setLevel(logging.INFO)
        handler.setLevel(logging.INFO)

    try:
        query: DblpQuery = DblpQuery(args, logger)
    except NoFileExistsError as e:
        sys.stderr.write("No such file: " + e.path)
        return 1

    if query.title is None:
        print("No title info: " + args.query)
        return 0

    logger.info("Building a query: " + str(query))

    try:
        article_entries: List[etree._Element] = download_article_entries(query.url, logger)
    except DownloadError as e:
        sys.stderr.write(str(e))
        return 1

    entries_len = len(article_entries)

    if entries_len == 0:
        print("No matches: " + str(query))
        return 0

    entry_num_limit = args.number
    selected_index = 0

    if entries_len > 1:
        print("\nMultiple results:\n")
        for i in range(min(entry_num_limit, entries_len)):
            print(f"({str(i)}) {format_article_entry(article_entries[i])}")

        if entries_len > entry_num_limit:
            print("and more omitted results...")

        while True:
            print("\nInput an entry index (Ctrl-D to exit):")

            try:
                s = input("> ")
            except EOFError:
                return 1

            try:
                i = int(s)
            except ValueError:
                continue

            if i < 1 or i >= min(entry_num_limit, entries_len):
                continue

            selected_index = i
            break

    bib_page_url: str = get_bib_page_url(article_entries[selected_index])

    try:
        bibtext: str = download_bib_text(bib_page_url, logger)
    except DownloadError as e:
        sys.stderr.write(str(e))
        return 1

    print(bibtext)
    return 0
