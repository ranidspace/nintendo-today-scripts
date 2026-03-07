# Filename: all_news.py
# Author: Ranidspace
# Description: Downloads all the daily videos shown on the Nintendo Today app

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from auth import create_session, update_token
from get_feed import download_individual


def parse_args():
    """Parse command line options"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--locale",
        default="en-US",
        help="Language and locale of the calendar, default en-US",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    locale = args.locale

    base_url = f"https://prod-server.de4taiqu.srv.nintendo.net/{locale}/"
    news_url = base_url + "news_contents/"
    contents_url = base_url + "contents/"

    s = create_session()
    if s is None:
        return 1

    response = s.get(news_url)

    news = response.json()

    for post_id in news["all_content_ids"]:
        post_response = s.get(contents_url + post_id)
        if not post_response.ok:
            # retry
            print(
                "Error getting post data, attempting to update token.",
                file=sys.stderr,
            )
            s = update_token(s)
            if s is None:
                return 1
            post_response = s.get(contents_url + post_id)
            if not post_response.ok:
                print(f"Failed: {post_response.text}", file=sys.stderr)
                return 1

        post_data = post_response.json()
        print("Found post: " + post_data["user_content"]["content"]["title"])

        timestamp = post_data["user_content"]["content"]["opened_at"]
        time = datetime.fromtimestamp(timestamp, UTC).isoformat()[:10]
        path = Path("./news").joinpath(f"{time} - {post_id}")

        if path.exists():
            print("Data exists, skipping.")
            continue

        path.mkdir(parents=True, exist_ok=True)
        response = download_individual(post_data, s, locale, path)

        if response is not None:
            # retry
            print(
                "Error downloading media, attempting to update token.",
                file=sys.stderr,
            )
            s = update_token(s)
            if s is None:
                return 1
            response = download_individual(post_data, s, locale)
            if response is not None:
                print(f"Unrecoverable error: {response.text}", file=sys.stderr)
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
