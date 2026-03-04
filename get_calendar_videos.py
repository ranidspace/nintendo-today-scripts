#!/usr/bin/env python
# Filename: get_calendar_videos.py
# Author: Ranidspace
# Description: Downloads all the daily videos shown on the Nintendo Today app

import argparse
import sys
from pathlib import Path

import requests

from auth import create_session


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--locale",
        default="en-US",
        help="Language and locale of the calendar, default en-US",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    locale = args.locale

    session = create_session()
    if session is None:
        return 1

    # not sure if other locales have differnet numbers, the birthday ones might
    # be different as well
    link = f"https://prod-server.de4taiqu.srv.nintendo.net/{locale}/calendars/all"

    response = session.get(link)

    if not response.ok:
        print(
            f"Failed to get calendars: Error {response.status_code}\n{response.json()}"
        )
        return 1

    j = response.json()

    animpath = Path("./calendars/animation")
    thumbpath = Path("./calendars/thumbnail")
    animpath.mkdir(parents=True, exist_ok=True)
    thumbpath.mkdir(parents=True, exist_ok=True)

    for cal in j["calendars"]:
        filepath = animpath.joinpath(f"{cal['id']}.mov")
        if filepath.is_file():
            continue
        link = cal["animation_url"]

        link = link.replace("-tiny.mov", "-large.mov")
        link = link.replace("-small.mov", "-large.mov")
        link = link.replace("-medium.mov", "-large.mov")
        r = requests.get(link, timeout=1)
        if r.ok:
            filepath.write_bytes(r.content)
        else:
            print(f"Error downloading: {r.text}")
            return 1

        filepath = thumbpath.joinpath(f"{cal['id']}.webp")
        link = cal["thumbnail_url"]
        link = link.replace("-tiny.webp", "-large.webp")
        link = link.replace("-small.webp", "-large.webp")
        link = link.replace("-medium.webp", "-large.webp")
        r = requests.get(link, timeout=1)
        if r.ok:
            filepath.write_bytes(r.content)
        else:
            print(f"Error downloading: {r.text}")
            return 1

    return 0


sys.exit(main())
