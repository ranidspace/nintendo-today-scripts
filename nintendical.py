#!/usr/bin/env python
# Filename: nintendical.py
# Author: Ranidspace
# Description: Exports all the Nintendo Today calendars to .ics files

import argparse
import os
import sys
from datetime import date, datetime, timedelta

import icalendar
import requests

__version__ = "0.0.1"


def parse_args():
    """Parse command line options"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--locale",
        default="en-US",
        help="Language and locale of the calendar, default en-US",
    )
    parser.add_argument(
        "-s",
        "--start-date",
        default=(datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d"),
        help="Start of calendar, format YYYY-MM-DD. Default: 30 days ago",
    )
    parser.add_argument(
        "-e",
        "--end-date",
        default=(datetime.today() + timedelta(days=365)).strftime("%Y-%m-%d"),
        help="End of calendar, format YYYY-MM-DD. Default: 365 days from now",
    )
    return parser.parse_args()


def main():
    """Main function to setup"""

    args = parse_args()
    cal_start = args.start_date
    cal_end = args.end_date
    locale = args.locale

    access_token = input("Input access_token: ")

    payload = {"start_date": cal_start, "end_date": cal_end}

    header = {
        "authorization": f"Bearer {access_token}",
        "operating-system": "android",
        "application-version": "1.0.2",
    }

    link = (
        "https://prod-server.de4taiqu.srv.nintendo.net/" + locale + "/event_schedules"
    )

    response = requests.get(link, params=payload, headers=header)

    if response.status_code != 200:
        print(f"Failed to get events: Error {response.status_code}\n{response.json()}")
        return 1

    n_cal = response.json()

    # init calendar
    current_time = datetime.now()
    calendar_list = {}
    ids = []

    for day in n_cal["calendars"]:
        event_date = day["date"]

        for n_event in day["event_schedules"]:
            # Multi-day events show up as one per day, filter out duplicates
            if n_event["id"] in ids:
                continue
            ids.append(n_event["id"])

            # Initialize event
            event = icalendar.Event()
            schedule = n_event["event_schedule"]

            # Add required args
            event.add("uid", n_event["id"])
            event.add("dtstamp", current_time)

            if schedule["all_day"]:
                datelist = [int(x) for x in event_date.split("-")]
                event.add("dtstart", date(*datelist))
            else:
                start = datetime.fromtimestamp(schedule["started_at"])
                event.add("dtstart", start)

                # if there's no end date, just make the event last an hour
                if schedule["is_undefined_ended_at"]:
                    event.add("dtend", start + timedelta(hours=1))
                else:
                    event.add("dtend", datetime.fromtimestamp(schedule["ended_at"]))

            event.add("summary", schedule["name"])
            event.add("categories", schedule["category_name"])
            event.add("categories", schedule["large_category"])
            if schedule.get("is_other_event"):
                event.add("categories", "Other Event")

            # Currently unused, may be used in the future
            # event.add("description", schedule["memo"])
            # event.add("url", schedule["link_content_id"]

            # Add event to a dict, to be added into a calendar later
            if schedule["category_name"] not in calendar_list:
                calendar_list[schedule["category_name"]] = []
            calendar_list[schedule["category_name"]].append(event)

    dir = "./calendars"
    if not os.path.exists(dir):
        os.makedirs(dir)
    for name, events in calendar_list.items():
        # Prepare calendar, not sure if I did prodid right
        cal = icalendar.Calendar()
        cal.add("prodid", f"-//nintendical//{__version__}//EN")
        cal.add("version", "2.0")

        for event in events:
            cal.add_component(event)

        # TODO make this filename safe, but works fine so far
        with open(os.path.join(dir, f"{name}.ics"), "wb") as f:
            f.write(cal.to_ical())
    return 0


sys.exit(main())
