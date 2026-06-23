# Filename: get_page.py
# Author: Ranidspace
# Description: Downloads an .html page and all assets from Nintendo Today
import asyncio
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from aiofile import async_open
from bs4 import BeautifulSoup, Tag
from niquests import AsyncSession, Response


async def save_content(output_dir: Path, save_path: Path, req: Response):
    """Save existing request content to disk"""
    outpath = output_dir.joinpath(save_path)
    Path(outpath).parent.mkdir(parents=True, exist_ok=True)
    if req.content is not None:
        outpath.write_bytes(req.content)


async def download_content(output_dir: Path, save_path: Path, file_url: str, session: AsyncSession):
    """Save existing request content to disk"""
    outpath = output_dir.joinpath(save_path)
    Path(outpath).parent.mkdir(parents=True, exist_ok=True)
    req = await session.get(file_url)
    if req.ok and req.content is not None:
        async with async_open(outpath, "wb") as afp:
            await afp.write(req.content)


async def get_css_images(
    base_url: str,
    css_rel_path: Path,
    css_data: bytes,
) -> list[tuple[Path, str]]:
    """Download linked images in css files"""
    # this is so jank
    regex = rb'(url\("?)(.*?)("?\))'
    matches = re.findall(regex, css_data)
    # All images have been webp so far should be fine
    urls = [k[1] for k in matches if b"webp" in k[1]]
    parent = Path(css_rel_path).parent
    return [(rel, urljoin(base_url, str(rel))) for rel in [parent.joinpath(url.decode("utf-8")) for url in urls]]


async def save_page(page_url: str, cookie: str, output_dir: Path, title="index"):
    # convert all image links to large images
    async with AsyncSession() as session:
        session.headers["cookie"] = cookie
        html = (await session.get(page_url)).content
        if html is None:
            return

        html = html.replace(b"-tiny.webp", b"-large.webp")
        html = html.replace(b"-small.webp", b"-large.webp")
        html = html.replace(b"-medium.webp", b"-large.webp")

        downloads: list[tuple[Path, str]] = []

        output_dir.mkdir(exist_ok=True)

        # Create filename safe title
        title = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "", title)
        title = title.replace(r"/\s\s+/g", " ").strip()

        soup = BeautifulSoup(html, "html.parser")
        locale = str(soup.html.get("lang")) or "en-US"
        for css in soup.find_all("style"):
            downloads += await get_css_images(page_url, Path("./"), css.encode())

        # XXX: this assumes all things with a link tag are css files.
        for link in soup.find_all("link"):
            if href := link.attrs.get("href"):
                href = str(href)

                if urlsplit(href).scheme:
                    continue

                # urljoin seems to be smart and not include the filename, yay!
                relative_path = Path(href)
                file_url = urljoin(page_url, href)
                downloads.append((relative_path, file_url))

                css = await session.get(file_url)
                if css.ok and css.content:
                    await save_content(output_dir, relative_path, css)
                    downloads += await get_css_images(page_url, relative_path, css.content)

        async def add_inline_link(content: Tag, attribute: str, local=False):
            if relative_path := str(content.get(attribute) or ""):
                if urlsplit(relative_path).scheme:
                    if local:
                        return
                    file_url = relative_path
                    base_path = urlsplit(relative_path).path
                    relative_path = Path(base_path).relative_to("/")

                    content[attribute] = str(relative_path)
                else:
                    if relative_path[0] == "/":
                        return
                    if relative_path[:2] != "./":
                        relative_path = "./" + relative_path
                        content[attribute] = str(relative_path)
                    file_url = urljoin(page_url, relative_path)
                downloads.append((Path(relative_path), file_url))

            # Instead of being in the "src" it's dynamically grabbed from js
            # JS files are grabbed now, but they don't seem to work
            elif data_file := str(content.get("data-file") or ""):
                relative_path = f"./assets/img/lang/{locale}/{data_file}"
                content[attribute] = str(relative_path)
                file_url = urljoin(page_url, relative_path)
                downloads.append((Path(relative_path), file_url))

        for img in soup.find_all("img"):
            await add_inline_link(img, "src")

        for video in soup.find_all("video"):
            # get poster
            await add_inline_link(video, "poster")

            # get video
            if vid := video.find("source"):
                await add_inline_link(vid, "src")

        for script in soup.find_all("script"):
            await add_inline_link(script, "src", local=True)

        async with async_open(output_dir.joinpath(f"{title}.html"), "w") as afp:
            await afp.write(str(soup))

        await asyncio.gather(*(download_content(output_dir, dl[0], dl[1], session) for dl in downloads))

        # TODO: get javascript files
        # not really needed since it seems to be app-related only.


def from_json(json, _, path: Path) -> None:
    """Download page from /contents/[id] json"""
    url = json["user_content"]["content"]["content_body_url"]
    title = json["user_content"]["content"]["title"]
    # create new session to fix an issue?
    cookie = "__token__=" + json["user_content"]["content"]["akamai_token"]

    asyncio.run(save_page(url, cookie, path, title))


def main():
    base_url = input("Input page URL: ")
    cookie = input("Input cookie: ")

    asyncio.run(save_page(base_url, cookie, Path("./site/")))

    return 0


if __name__ == "__main__":
    sys.exit(main())
