#!/usr/bin/env python
# Filename: get_calendar_videos.py
# Author: Ranidspace
# Description: Downloads all the daily videos shown on the Nintendo Today app

import argparse
import os
import sys

import requests


def parse_args():
    """Parse command line options"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l", "--locale",
        default="en-US",
        help="Language and locale of the calendar, default en-US"
    )
    return parser.parse_args()


def main():
    """Main function to setup"""

    args = parse_args()
    locale = args.locale

    access_token = input("Input access_token: ")

    header = {
        "authorization": f"Bearer {access_token}",
        "time_zone": "America/Chicago",
        "operating-system": "android",
        "application-version": "1.0.0",
    }

    # not sure if other locales have differnet numbers, the birthday ones might
    # be different as well
    link = f"https://prod-server.de4taiqu.srv.nintendo.net/{locale}/calendars/all"

    response = requests.get(link, headers=header)

    if response.status_code != 200:
        print(f"Failed to get calendars: Error {response.status_code}\n{response.json()}")
        return 1

    j = response.json()

    os.makedirs("./animation", exist_ok=True)
    os.makedirs("./thumbnail", exist_ok=True)

    for cal in j["calendars"]:
        link = cal["animation_url"]

        link = link.replace("-tiny.mov", "-large.mov")
        link = link.replace("-small.mov", "-large.mov")
        link = link.replace("-medium.mov", "-large.mov")
        r = requests.get(link)
        with open(os.path.join("./animation", f"{cal["id"]}.mov"), "wb") as f:
            f.write(r.content)

        link = cal["thumbnail_url"]
        link = link.replace("-tiny.webp", "-large.webp")
        link = link.replace("-small.webp", "-large.webp")
        link = link.replace("-medium.webp", "-large.webp")
        r = requests.get(link)
        with open(os.path.join("./thumbnail", f"{cal["id"]}.webp"), "wb") as f:
            f.write(r.content)

    return 0


sys.exit(main())
