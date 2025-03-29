#!/usr/bin/env python
# Filename: get_page.py
# Author: Ranidspace
# Description: Downloads an .html page and all assets from Nintendo Today

import os
import pathlib
import re
import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup as bs


def get_css_images(session, links, base_url, relative, css):
    """Download linked images in css files"""
    # this is so jank
    regex = b'(?<=url\\(")(.*)(?="\\))'
    urls = re.findall(regex, css)
    for url in urls:
        # All images have been webp so far should be fine
        if b'webp' in url:
            parent = pathlib.Path(relative).parent
            rel = os.path.join(parent, url.decode("utf-8"))
            rel = os.path.normpath(rel)
            file_url = urljoin(base_url, rel)
            image = session.get(file_url).content
            links.append((rel, image))


def main():
    """Main function to setup"""

    base_url = input("Input page URL: ")
    session = requests.Session()
    session.headers["cookie"] = input("Input cookie: ")

    # convert all image links to large images
    html = session.get(base_url).content
    html = html.replace(b"-tiny.webp", b"-large.webp")
    html = html.replace(b"-small.webp", b"-large.webp")
    html = html.replace(b"-medium.webp", b"-large.webp")

    # Save the original html file
    os.makedirs("./site", exist_ok=True)
    with open(os.path.join("./site", "index.html"), "wb") as f:
        f.write(html)

    soup = bs(html, "html.parser")

    links = []

    # download stylesheets
    # XXX: this assumes all things with a link tag are css files.
    for link in soup.find_all("link"):
        if link.attrs.get("href"):
            relative = link.attrs.get("href")

            # urljoin seems to be smart and not include the filename, yay!
            file_url = urljoin(base_url, relative)

            css = session.get(file_url).content
            css = css.replace(b"-tiny.webp", b"-large.webp")
            css = css.replace(b"-small.webp", b"-large.webp")
            css = css.replace(b"-medium.webp", b"-large.webp")
            get_css_images(session, links, base_url, relative, css)
            links.append((relative, css))

    # get images from the html files
    for img in soup.find_all('img'):
        if img.get("src"):
            relative = img["src"]
            file_url = urljoin(base_url, relative)
            image = session.get(file_url).content
            links.append((relative, image))

    # TODO: get javascript files
    # not really needed since it seems to be app-related only.

    # Save each file in the proper position
    for link in links:
        path = os.path.join("./site", link[0])
        path = os.path.normpath(path)
        os.makedirs(pathlib.Path(path).parent, exist_ok=True)
        with open(path, "wb") as f:
            f.write(link[1])

    return 0


sys.exit(main())
