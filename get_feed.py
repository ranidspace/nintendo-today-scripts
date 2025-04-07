#!/usr/bin/env python
# Filename: get_feed.py
# Author: Ranidspace
# Description: Download all items in a content feed

import argparse
import os
import sys
import subprocess
from urllib.parse import urlparse

import requests

from get_page import from_json


def download_video(info, s):
    """Use system ffmpeg to get the video"""
    url = info["user_content"]["content"]["content_movie_url"]
    title = info["user_content"]["content"]["title"]
    # Needs a better solution to ensure the filename is safe
    title = title.replace("/", "").replace("  ", " ")

    token = info["user_content"]["content"]["akamai_header_token"]

    print(f"\tDownloading Video: {title}.mp4")
    # get the video file with the headers, copy the video and audio codec
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-y",
            "-headers", f'__token__: {token}',
            "-i", url,
            "-c", "copy",
            f"videos/{title}.mp4"
        ],
    )


def download_images(info, s):
    """Get all images in a gallery post"""
    for url in info["user_content"]["content"]["content_image_urls"]:
        # Ensure large image
        url = url.replace("-small.", "-large.")
        fname = os.path.basename(urlparse(url).path)
        title = info["user_content"]["content"]["title"]
        print(f"\tDownloading image: {title}")

        # XXX: Doesn't check if filename is safe
        os.makedirs(f"./images/{title}", exist_ok=True)

        # Download and save image with a different session
        r = requests.get(url)
        with open(os.path.join(f"./images/{title}", fname), "wb") as f:
            f.write(r.content)


def parse_args():
    """Parse command line options"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "id",
        help="ID of the first entry in the feed"
    )
    parser.add_argument(
        "-l", "--locale",
        default="en-US",
        help="Language and locale of the calendar, default en-US"
    )
    parser.add_argument(
        "-b", "--browsing_history",
        action="store_true",
        help="Add the content to the apps browsing_history"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    locale = args.locale
    hist = args.browsing_history
    id = args.id

    access_token = input("Input access_token: ")

    header = {
        "authorization": f"Bearer {access_token}",
        "time_zone": "America/Chicago",
        "operating-system": "android",
        "application-version": "1.0.0",
    }
    s = requests.Session()
    s.headers.update(header)

    base = f"https://prod-server.de4taiqu.srv.nintendo.net/{locale}/"
    base_contents = base + "contents/"
    base_hist = base + "browsing_history/"

    try:
        # Get type of url
        response = s.get(base_contents + id)
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
    match j["user_content"]["content"]["content_type"]:
        case 1:
            func = from_json
        case 2:
            func = download_video
            os.makedirs("./videos", exist_ok=True)
        case 3:
            func = download_images
            os.makedirs("./images", exist_ok=True)

    # Run until there's no more next content
    # TODO: Fetch previous feed items
    while id:
        j = s.get(base_contents + id).json()
        print(f"Found entry: {j["user_content"]["content"]["title"]}")
        if hist:
            s.put(base_hist + id)

        func(j, s)

        if j.get("series_info"):
            id = j["series_info"].get("next_content_id")
            if id is None:
                print("No more entries, exiting.")
        else:
            print("Not a series, exiting.")
            break


if __name__ == "__main__":
    main()
