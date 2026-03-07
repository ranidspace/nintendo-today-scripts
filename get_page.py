# Filename: get_page.py
# Author: Ranidspace
# Description: Downloads an .html page and all assets from Nintendo Today
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
from requests import Response, Session


def download_content(output_dir: Path, save_path: Path, req: Response):
    outpath = output_dir.joinpath(save_path)
    Path(outpath).parent.mkdir(parents=True, exist_ok=True)
    outpath.write_bytes(req.content)


def get_css_images(
    session: Session,
    output_dir: Path,
    base_url: str,
    css_rel_path: Path,
    css_data: bytes,
):
    """Download linked images in css files"""
    # this is so jank
    regex = rb'(url\("?)(.*?)("?\))'
    matches = re.findall(regex, css_data)
    for match in matches:
        # All images have been webp so far should be fine
        url = match[1]
        if b"webp" in url:
            # URLs in CSS are relative to the css file itself
            parent = Path(css_rel_path).parent
            rel = parent.joinpath(url.decode("utf-8"))
            file_url = urljoin(base_url, str(rel))
            image = session.get(file_url)
            if image.ok:
                download_content(output_dir, rel, image)


def save_page(page_url: str, session: Session, output_dir: Path, title="index"):
    # convert all image links to large images
    html = session.get(page_url).content

    html = html.replace(b"-tiny.webp", b"-large.webp")
    html = html.replace(b"-small.webp", b"-large.webp")
    html = html.replace(b"-medium.webp", b"-large.webp")

    output_dir.mkdir(exist_ok=True)

    # Create filename safe title
    title = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "", title)
    title = title.replace(r"/\s\s+/g", " ").strip()
    output_dir.joinpath(f"{title}.html").write_bytes(html)

    soup = BeautifulSoup(html, "html.parser")

    # XXX: this assumes all things with a link tag are css files.
    for link in soup.find_all("link"):
        if href := link.attrs.get("href"):
            href = str(href)

            if urlsplit(href).scheme:
                continue

            # urljoin seems to be smart and not include the filename, yay!
            relative_path = Path(href)
            file_url = urljoin(page_url, href)

            css = session.get(file_url)
            if css.ok:
                download_content(output_dir, relative_path, css)
                get_css_images(session, output_dir, page_url, relative_path, css.content)

    def download_inline_link(content, attribute: str):
        if relative_path := content.get(attribute):
            relative_path = content.get(attribute)
            file_url = urljoin(page_url, relative_path)
            image = session.get(file_url)
            if image.ok:
                download_content(output_dir, Path(str(relative_path)), image)

    for img in soup.find_all("img"):
        download_inline_link(img, "src")

    for video in soup.find_all("video"):
        # get poster
        download_inline_link(video, "poster")

        # get video
        if vid := video.find("source"):
            download_inline_link(vid, "src")

    # TODO: get javascript files
    # not really needed since it seems to be app-related only.


def from_json(json, _, path: Path) -> None:
    """Download page from /contents/[id] json"""
    url = json["user_content"]["content"]["content_body_url"]
    title = json["user_content"]["content"]["title"]
    # create new session to fix an issue?
    s = Session()
    s.headers["cookie"] = "__token__=" + json["user_content"]["content"]["akamai_token"]

    save_page(url, s, path, title)


def main():
    base_url = input("Input page URL: ")
    session = Session()
    session.headers["cookie"] = input("Input cookie: ")

    save_page(base_url, session, Path("./site/"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
