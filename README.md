# Nintendo Today Scripts

This repo contains a couple scripts I've made to download or convert data from
the Nintendo Today mobile app.

Each script has it's own dependencies, however `pip install -r
requirements.txt` gets the dependencies for all of them.

## nintendical

Converts your Calendar in the nintendo app to a set of .ics files, to be
imported into a calendar app of your choice. If hosted on a server, the files
can be updated and the calendar will update in the app.

### Usage

```
python nintendical.py -s [start date] -e [end date] -l [locale]
```

The start and end date must be in the form YYYY-MM-DD, and the locale is in the
form `en-US`. Many common locales are not supported by the app yet.

If omitted, the start date will be one month from the current day, the end date
will be a year from the current date, and the locale will be `en-US`.

After running the command it will ask for an access token, please see [the
section on intercepting phone traffic](#intercept-phone-traffic) for guidance.

Requests to the app will often contain an `authorization` header which begins
with `Bearer` (do not include "Bearer").

It should also be in the response of requests to a url ending in "auth/refresh"

Requires `requests, icalendar` modules

## get_calendar_videos

Downloads all the daily videos for all app themes. Will also include the
birthday videos for the day of the month your birthday is. The access token is
the same as the Nintendical one.

### Usage
```
python get_calendar_videos.py -l [locale]
```
Locale option is the same as nintendical. It will ask for an access token,
which is also the same.

Requires `requests` module

## get_page

Some of the news posts are html files, this will download the html file, along
with any css and images linked. This will also upgrade the quality to the
"large" format.

### Usage
```
python get_page.py
```

The web request for the html file on the app includes a cookie header, which
begins with `__token__=exp=`, include the full cookie.

Requires `requests, beautifulsoup4` modules.

## Download news videos

No script needed, the video files are "master.m3u8" and can be downloaded with
ffmpeg:

```
ffmpeg -headers "__token__: [add token here]" -i https://[link/to]/master.m3u8 output.mkv`
```

The token needed is inside of the header for the web request.

## Intercept phone traffic

Not for Nintendo Today specifically but it is needed to get the links and
tokens for all of the scripts.

iOS users can install certificates without root, and you can follow the guide
[Setting up mitmproxy with
iOS](https://www.trickster.dev/post/setting-up-mitmproxy-with-ios17.1/). I've
not tried it out but others have said it worked for them.

A rooted android device can also install System CA certificates, if you have
access to neither, an android Emulator on your computer should work.

I have had luck with Waydroid on Linux and Android Studio on Windows. I have
heard others had success with mumuplayer. If you're on android studio, set the
AVD to be `Pixel 6, API 33 Tiramisu`. For any android emulator try to download
it without google services.

1. Install mitmproxy to your computer, and add the System CA certificate to the
device

If you install and run mitmproxy, a `.mitmproxy` should appear in your home
directory containing `mitmproxy-ca-cert.pem`. Adding the certificate is
different for every device and emulator. 

- [Android
studio](https://docs.mitmproxy.org/stable/howto-install-system-trusted-ca-android/)
- [Waydroid](https://github.com/casualsnek/waydroid_script) (see "install a
self signed certificate)
- [mumuplayer](https://www.mumuplayer.com/mac/tutorials/certificates-and-packet-capture.html)

2. Install the Nintendo today app

The app comes as a split apk, so you may need something such as an xapk
installer, AntiSplit M, or you can install the app directly from Aurora Store
(try version 4.2.5 if it crashes on the emulator).

3. Run mitmweb and connect the device to it

You can connect the device to mitmweb by adding it as a proxy on your phone.
Find the local ip address of your computer and the port (8080 by default) and
use that. You can also run mitmweb as a wireguard server, and you can install
the wireguard app on the device, and connect to it there.

4. Confirm you're intercepting web traffic

As you use your device and the app the "Flow List" tab of mitmweb should start
to fill with entries. These are the requests, you can click on one and view the
request (includes the headers, tokens, cookies) and the response (data received
back from the server, such as images)

If you're not receiving data on mitmweb, it's likely you need to configure your
connection to the proxy. If you are receiving data, but you're unable to use
the app or any https websites, it's likely your device doesn't have the
certificate.
