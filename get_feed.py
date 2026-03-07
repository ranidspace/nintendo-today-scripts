# Filename: get_feed.py
# Author: Ranidspace
# Description: Download all items in a content feed

import argparse
import re
import sys
from pathlib import Path

import ffmpeg
import requests

from auth import create_session, update_token
from get_page import from_json


def download_video(
    info,
    session: requests.Session,
    path: Path,
    locale: str,
) -> requests.Response | None:
    """Use system ffmpeg to get the video"""
    url = info["user_content"]["content"]["content_movie_url"]
    title = info["user_content"]["content"]["title"]
    category = info["user_content"]["content"].get("content_group_name")
    if category:
        title = f"{category} - {title}"

    # Make title filename safe
    title = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    title += ".mkv"

    token = info["user_content"]["content"]["akamai_header_token"]

    if info["user_content"]["content"]["is_premiere"]:
        post_id = info["user_content"]["id"]
        premiere = session.get(
            f"https://prod-server.de4taiqu.srv.nintendo.net/{locale}/contents/{post_id}/premiere",
        )
        if not premiere.ok:
            return premiere
        premiere = premiere.json()
        url = premiere["premiere"]["content_movie_url"]
        token = premiere["premiere"]["cdn_header_token"]
    output = path.joinpath(title)

    print(f"\tDownloading Video: {title}")

    ffmpeg.input(url, headers=f"__token__: {token}").output(
        str(output),
        codec="copy",
    ).run(capture_stderr=True, overwrite_output=True)
    return None


def download_images(info: dict, _, path: Path) -> requests.Response | None:
    """Get all images in a gallery post"""
    urls = info["user_content"]["content"]["content_image_urls"]
    group = info["user_content"]["content"].get("content_group_name")
    title = info["user_content"]["content"]["title"]
    # make filename safe
    title = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "", title)
    title = re.sub(r"\s+", " ", title)

    for i in range(len(urls)):
        # Ensure large image
        url = urls[i].replace("-small.", "-large.")
        suffix = Path(url.split("?")[0]).suffix
        if group:
            title = f"{group} - {title}"
        if len(urls) > 1:
            title += f" - {i + 1}"
        title += suffix
        print(f"\tDownloading image: {title}")

        # Download and save image with a unique session
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        outdir = path.joinpath(title)
        outdir.write_bytes(r.content)
    return None


def download_individual(
    json_info: dict,
    session: requests.Session,
    locale: str,
    path: Path | None = None,
) -> requests.Response | None:
    post_content = json_info["user_content"]["content"]

    # 1: HTML page
    # 2: Video
    # 3: Series of images
    match post_content["content_type"]:
        case 1:
            path = path or Path("./site/")
            return from_json(json_info, session, path)
        case 2:
            path = path or Path("./videos/")
            return download_video(json_info, session, path, locale)
        case 3:
            path = path or Path("./images/")
            return download_images(json_info, session, path)


def parse_args():
    """Parse command line options"""
    parser = argparse.ArgumentParser()
    parser.add_argument("id", help="ID of the first entry in the feed")
    parser.add_argument(
        "-l",
        "--locale",
        default="en-US",
        help="Language and locale of the calendar, default en-US",
    )
    parser.add_argument(
        "-b",
        "--browsing_history",
        action="store_true",
        help="Add the content to the apps browsing_history",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    locale = args.locale
    hist = args.browsing_history
    post_id = args.id

    s = create_session()

    if s is None:
        return 1

    base = f"https://prod-server.de4taiqu.srv.nintendo.net/{locale}/"
    base_contents = base + "contents/"
    base_hist = base + "browsing_history/"

    try:
        # Get type of url
        response = s.get(base_contents + post_id)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # Only doing a one check
        print("Failed to get entry", file=sys.stderr)
        print(e.args[0], file=sys.stderr)
        print(response.json(), file=sys.stderr)

        return 1

    j = response.json()

    if not j["user_content"]["content"]["content_group_id"]:
        print(f"Single Entry: {j['user_content']['content']['title']}")
        if hist:
            s.put(base_hist + post_id)
        download_individual(j, s, locale)
        return 0

    print("Finding first in series:")
    # Run until there's no more next content
    # Find previous
    while prev_post_id := j["user_content"]["content"]["prev_content_id"]:
        print(j["user_content"]["content"]["content_group_number"])
        j = s.get(base_contents + prev_post_id).json()

    while post_id:
        print(f"Found entry: {j['user_content']['content']['title']}")
        if hist:
            s.put(base_hist + post_id)

        response = download_individual(j, s, locale)

        if response is not None:
            # retry
            print(
                "Error downloading media, attempting to update token.", file=sys.stderr
            )
            s = update_token(s)
            if s is None:
                return 1
            response = download_individual(j, s, locale)
            if response is not None:
                print(f"Unrecoverable error: {response.text}", file=sys.stderr)
                return 1

        post_id = j["user_content"]["content"]["next_content_id"]
        # XXX: This is stupid but it avoids having to re-request
        # the same thing mutliple times
        if not post_id:
            print("No more entries, exiting.")
        else:
            req = s.get(base_contents + post_id)
            if not req.ok:
                print("Fetching post data failed, refreshing token")
                s = update_token(s)
                if s is None:
                    return 1
            j = req.json()
    return 0


if __name__ == "__main__":
    sys.exit(main())
