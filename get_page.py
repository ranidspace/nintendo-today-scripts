#!/usr/bin/env python
# Filename: get_page.py
# Author: Ranidspace
# Description: Downloads an .html page and all assets from Nintendo Today

import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def get_css_images(session, links, base_url, relative, css):
    """Download linked images in css files"""
    # this is so jank
    regex = b'(?<=url\\(")(.*)(?="\\))'
    urls = re.findall(regex, css)
    for url in urls:
        # All images have been webp so far should be fine
        if b"webp" in url:
            parent = Path(relative).parent
            rel = parent / url.decode("utf-8")
            file_url = urljoin(base_url, str(rel))
            image = session.get(file_url).content
            links.append((rel, image))


def save_page(url, session, title="index"):
    # convert all image links to large images
    html = session.get(url).content
    html = html.replace(b"-tiny.webp", b"-large.webp")
    html = html.replace(b"-small.webp", b"-large.webp")
    html = html.replace(b"-medium.webp", b"-large.webp")

    # Save the original html file
    Path("./site").mkdir(exist_ok=True)
    # Create filename safe title
    title = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "", title)
    title = title.replace(r"/\s\s+/g", " ")
    Path(f"./site/{title}.html").write_bytes(html)

    soup = BeautifulSoup(html, "html.parser")

    links = []

    # download stylesheets
    # XXX: this assumes all things with a link tag are css files.
    for link in soup.find_all("link"):
        if link.attrs.get("href"):
            relative = link.attrs.get("href")

            # urljoin seems to be smart and not include the filename, yay!
            file_url = urljoin(url, relative)

            css = session.get(file_url).content
            css = css.replace(b"-tiny.webp", b"-large.webp")
            css = css.replace(b"-small.webp", b"-large.webp")
            css = css.replace(b"-medium.webp", b"-large.webp")
            get_css_images(session, links, url, relative, css)
            links.append((relative, css))

    # get images from the html files
    for img in soup.find_all("img"):
        if img.get("src"):
            relative = img["src"]
            file_url = urljoin(url, relative)
            image = session.get(file_url).content
            links.append((relative, image))

    # TODO: get javascript files
    # not really needed since it seems to be app-related only.

    # Save each file in the proper position
    for link in links:
        path = Path("./site") / link[0]
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(link[1])


def from_json(json, _):
    """Download page from /contents/[id] json"""
    url = json["user_content"]["content"]["content_body_url"]
    title = json["user_content"]["content"]["title"]
    # create new session to fix an issue?
    s = requests.Session()
    s.headers["cookie"] = "__token__=" + json["user_content"]["content"]["akamai_token"]

    save_page(url, s, title)


def main():
    """Main function to setup"""
    base_url = input("Input page URL: ")
    session = requests.Session()
    session.headers["cookie"] = input("Input cookie: ")

    save_page(base_url, session)

    return 0


if __name__ == "__main__":
    sys.exit(main())
