import argparse
import os
import sys
import urllib.parse

from lxml import html
from PyPDF2 import PdfFileReader
import pyperclip
import requests

from .exceptions import *


class Query:
    def __init__(self, args):
        if args.file:
            self.title = extract_title_from_pdf(args.query)
        else:
            self.title = args.query

        self.author = args.author
        self.year = args.year
        self.venue = args.venue
        self.conf = args.conf
        self.journal = args.journal


    def __str__(self):
        s = self.title

        for author in self.author:
            s += " " + author

        s += f" year:{str(self.year)}:" if self.year else ""
        s += f" venue:{self.venue}:" if self.venue else ""

        if self.conf:
            s += " type:Conference_and_Workshop_Papers:"

        if self.journal:
            s += " type:Journal_Articles:"

        return s


def extract_title_from_pdf(path):
    if not os.path.isfile(path):
        raise NoFileExistsError(path)

    f = open(path, 'rb')
    info = PdfFileReader(f).getDocumentInfo()

    if info is None or info.title is None:
        raise NoTitleExistsError(path)

    return info.title


def get_bib_page_url(query):
    try:
        search_result_html = requests.get(
            "http://dblp.uni-trier.de/search?q=" + urllib.parse.quote(str(query))).text
    except:
        raise HttpGetError()

    root = html.fromstring(search_result_html)
    node_of_entries = root.xpath("//*[@class=\"publ\"]/ul/li[2]/div[1]/a")

    if len(node_of_entries) == 0:
        raise NoMatchError(query)

    return node_of_entries[0].attrib["href"]


def get_bib_text(url):
    try:
        bib_page_html = requests.get(url).text
    except:
        raise HttpGetError()

    root = html.fromstring(bib_page_html)
    return root.xpath("//*[@id=\"bibtex-section\"]/pre[1]")[0].text


def main():
    parser = argparse.ArgumentParser(description="Copy bibtex entry from DBLP")
    parser.add_argument("-f", "--file", action="store_true",
                        help="interpret query as file path")
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

    exit_status = 1

    try:
        query = Query(parser.parse_args())
        bib_page_url = get_bib_page_url(query)
        bibtext = get_bib_text(bib_page_url)
        pyperclip.copy(bibtext)
        sys.stdout.write("The following result is copied to the clipboard.")
        sys.stdout.write(bibtext)
        exit_status = 0
    except HttpGetError:
        sys.stderr.write("Failed to access the DBLP server.")
    except NoFileExistsError as err:
        sys.stderr.write(f"File \"{err.path}\" does not exist.")
    except NoTitleExistsError as err:
        sys.stderr.write(f"No title info is found in {err.path}")
    except NoMatchError as err:
        sys.stderr.write(f"No matches for \"{str(err.query)}\".")

    return exit_status
