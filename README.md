# Nintendo Today Scripts

This repo contains a couple scripts I've made to download or convert data from
the Nintendo Today mobile app.

## nintendical

Converts your Calendar in the nintendo app to a set of .ics files, to be
imported into a calendar app of your choice. If hosted on a server, the files
can be updated and the calendar will update in the app.

### Access token?

An access token is needed to get the calendar data. This can be found by
capturing the internet traffic from the app, which would require a rooted or
emulated android phone due to needing to install System CA certificates.

If you intercept the traffic, requests to the app will often contain an
`authorization` header which begins with `Bearer` (do not include "Bearer").

It should also be in the response of requests to a url ending in "auth/refresh"

### Required python packages

- icalendar
- requests

## get_calendar_videos

Downloads all the daily videos for all app themes. Will also include the
birthday videos for the day of the month your birthday is. The access token is
the same as the Nintendical one.

### Required python packages

- requests

## get_page

Some of the news posts are html files, and this will download the html file,
along with any css and images linked. This will also upgrade the quality to the
"large" format.

### Cookie?

The web request for the html file on the app includes a cookie header, which
begins with `__token__=exp=`, include the full cookie.

### Required python packages

- requests
- beautifulsoup4

## Download news videos?

No script needed, the video files are "master.m3u8" and can be downloaded with
ffmpeg using a `-headers` argument, with a link to it as the `-i` argument.
