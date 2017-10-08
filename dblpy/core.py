import argparse
import os
import sys
import urllib.parse

from lxml import html
from PyPDF2 import PdfFileReader
import pyperclip
import requests

from .exceptions import *


def extract_title_from_pdf(path):
    if not os.path.isfile(path):
        raise NoFileExistsError(path)

    f = open(path, 'rb')
    info = PdfFileReader(f).getDocumentInfo()

    if info is None or info.title is None:
        raise NoTitleExistsError(path)

    return info.title


def build_query(args):
    if args.file:
        query = extract_title_from_pdf(args.query)
    else:
        query = args.query

    if args.conf:
        query += " conference"
    elif args.journal:
        query += " journal"

    return query


def get_bib_page_url(query):
    try:
        search_result_html = requests.get(
            "http://dblp.uni-trier.de/search?q=" + urllib.parse.quote(query)).text
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
    parser.add_argument("query", type=str)
    parser.add_argument("-f", "--file", action="store_true")
    option_group = parser.add_mutually_exclusive_group()
    option_group.add_argument("-c", "--conf", action="store_true")
    option_group.add_argument("-j", "--journal", action="store_true")

    exit_status = 1

    try:
        query = build_query(parser.parse_args())
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
        sys.stderr.write(f"No matches for \"{err.query}\".")

    return exit_status
