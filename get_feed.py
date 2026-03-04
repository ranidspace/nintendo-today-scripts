#!/usr/bin/env python
# Filename: get_feed.py
# Author: Ranidspace
# Description: Download all items in a content feed

import argparse
import re
import sys
from pathlib import Path

import ffmpeg
import requests

from get_page import from_json


def download_video(info, session, locale):
    """Use system ffmpeg to get the video"""
    url = info["user_content"]["content"]["content_movie_url"]
    title = info["user_content"]["content"]["title"]
    # Make title filename safe
    title = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "", title)
    title = re.sub(r"\s+", " ", title)
    token = info["user_content"]["content"]["akamai_header_token"]

    if info["user_content"]["content"]["is_premiere"]:
        post_id = info["user_content"]["id"]
        premiere = session.get(
            f"https://prod-server.de4taiqu.srv.nintendo.net/{locale}/contents/{post_id}/premiere",
        ).json()
        url = premiere["premiere"]["content_movie_url"]
        token = premiere["premiere"]["cdn_header_token"]

    print(f"\tDownloading Video: {title}.mkv")

    # get the video file with the headers, copy the video and audio codec
    # TODO: Replace with ffmpeg-python
    ffmpeg.input(url, headers=f"__token__: {token}").output(
        f"videos/{title}.mkv",
        codec="copy",
    ).run(capture_stderr=True, overwrite_output=True)


def download_images(info, _):
    """Get all images in a gallery post"""
    urls = info["user_content"]["content"]["content_image_urls"]
    num = info["user_content"]["content"]["content_group_number"]
    img_num = ""
    title = info["user_content"]["content"]["title"]
    # make filename safe
    title = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "", title)
    title = re.sub(r"\s+", " ", title)

    for i in range(len(urls)):
        # Ensure large image
        url = urls[i].replace("-small.", "-large.")
        if len(urls) > 1:
            img_num = f".{i + 1}"
        fname = f"{num}{img_num} - {title}"
        print(f"\tDownloading image: {title}")

        # Download and save image with a unique session
        r = requests.get(url, timeout=5)
        outdir = Path("./images").joinpath(fname)
        outdir.with_suffix(outdir.suffix + ".webp").write_bytes(r.content)


def download_individual(json_info, session, locale):
    post_content = json_info["user_content"]["content"]
    match post_content["content_type"]:
        case 1:
            from_json(json_info, session)
        case 2:
            Path("./videos").mkdir(exist_ok=True)
            download_video(json_info, session, locale)
        case 3:
            Path("./images").mkdir(exist_ok=True)
            download_images(json_info, session)


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

    access_token = input("Input access_token: ")

    header = {
        "authorization": f"Bearer {access_token}",
        "time_zone": "America/Chicago",
        "operating-system": "android",
        "application-version": "2.4.0",
    }
    s = requests.Session()
    s.headers.update(header)

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

        sys.exit(1)

    j = response.json()

    # 1: HTML page
    # 2: Video
    # 3: Series of images

    if not j["user_content"]["content"]["content_group_id"]:
        print(f"Single Entry: {j['user_content']['content']['title']}")
        if hist:
            s.put(base_hist + post_id)
        download_individual(j, s, locale)
        return

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

        download_individual(j, s, locale)

        post_id = j["user_content"]["content"]["next_content_id"]
        # XXX: This is stupid but it avoids having to re-request
        # the same thing mutliple times
        if not post_id:
            print("No more entries, exiting.")
        else:
            j = s.get(base_contents + post_id).json()


if __name__ == "__main__":
    main()
