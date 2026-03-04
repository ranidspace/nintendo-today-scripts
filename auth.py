import json
import pathlib
import sys

import requests

REFRESH_URL = "https://prod-server.de4taiqu.srv.nintendo.net/en-US/auth/refresh"
CLIENT_FILE = pathlib.Path("./client.json")

HEADERS = {
    "time_zone": "America/Chicago",
    "operating-system": "android",
    "application-version": "2.4.0",
    "application-version-secret": "9iEfV3uen8MSShkF",
}


# This function assumes a file exists, as it should only be called after
# create_session has run
def update_token(session: requests.Session) -> requests.Session | None:
    """Update the authorization token, and write it to a file"""
    request_body = {}
    with CLIENT_FILE.open(encoding="utf-8") as fp:
        client = json.load(fp)

        request_body["refresh_token"] = client.get("refresh_token")
        request_body["device_account_id"] = client.get("device_account_id")

        if not any(request_body):
            # This doesn't write to the file, it happens later
            ask_for_client(request_body)

    response = session.post(
        REFRESH_URL,
        json=request_body,
    )

    if not response.ok:
        print(
            f"Bad response, may require manual editing: {response.request.headers}",
            file=sys.stderr,
        )
        return None

    token = response.json()["access_token"]

    with CLIENT_FILE.open(mode="w", encoding="utf-8") as fp:
        request_body["access_token"] = token
        json.dump(request_body, fp, indent=4)

    session.headers.update({"authorization": f"Bearer {token}"})
    return session


def ask_for_client(body: dict) -> None:
    body["refresh_token"] = input(
        "Input refresh_token from an /auth/refresh request: "
    ).strip()
    body["device_account_id"] = input("Input the device_account_id: ").strip()


def create_session() -> requests.Session | None:
    """Return a request session, an create or update a client.json file"""
    if not CLIENT_FILE.is_file():
        CLIENT_FILE.touch()
        CLIENT_FILE.write_text("{}", encoding="utf-8")

    session = requests.Session()
    session.headers.update(HEADERS)

    with CLIENT_FILE.open(encoding="utf-8") as fp:
        client = json.load(fp)

        if "access_token" not in client:
            return update_token(session)
        session.headers.update({"authorization": f"Bearer {client['access_token']}"})

    # Test access_token
    response = session.get("https://prod-server.de4taiqu.srv.nintendo.net/en-US/user")

    if response.ok:
        return session

    if "access_token" in session.headers:
        del session.headers["access_token"]
    return update_token(session)
