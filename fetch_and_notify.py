import os
import json
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText

import requests

# ---- Required environment variables (set as GitHub repo secrets) ----
CLIST_USERNAME = os.environ["CLIST_USERNAME"]
CLIST_API_KEY = os.environ["CLIST_API_KEY"]
GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
TO_EMAIL = os.environ.get("TO_EMAIL", GMAIL_ADDRESS)

# Optional: comma-separated clist "resource" names to restrict which judges
# you get reminders for, e.g. "codeforces.com,leetcode.com". Leave unset/empty
# to get reminders for every contest clist.by tracks.
RESOURCES = [r.strip() for r in os.environ.get("CLIST_RESOURCES", "").split(",") if r.strip()]

STATE_FILE = "state.json"
CLIST_API_URL = "https://clist.by/api/v4/contest/"

REMINDER_WINDOWS = {
    "24h": timedelta(hours=24),
    "6h": timedelta(hours=6),
}

# Cron runs every 15 min, so give a matching tolerance window around each
# threshold. A contest is reminded once time-until-start falls into
# (window - TOLERANCE, window].
TOLERANCE = timedelta(minutes=15)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def fetch_upcoming_contests():
    params = {
        "username": CLIST_USERNAME,
        "api_key": CLIST_API_KEY,
        "upcoming": "true",
        "format": "json",
        "order_by": "start",
        "limit": 100,
    }
    if RESOURCES:
        params["resource__in"] = ",".join(RESOURCES)

    resp = requests.get(CLIST_API_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("objects", [])


def parse_start(contest):
    raw = contest.get("start") or contest.get("start_time")
    if not raw:
        return None
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, [TO_EMAIL], msg.as_string())


def main():
    now = datetime.now(timezone.utc)
    state = load_state()
    contests = fetch_upcoming_contests()
    active_ids = set()

    for contest in contests:
        contest_id = str(contest.get("id"))
        active_ids.add(contest_id)

        start = parse_start(contest)
        if start is None:
            continue

        time_until = start - now
        if time_until.total_seconds() < 0:
            continue  # already started

        entry = state.get(contest_id, {"sent_24h": False, "sent_6h": False})

        for label, window in REMINDER_WINDOWS.items():
            key = f"sent_{label}"
            if entry.get(key):
                continue

            if window - TOLERANCE <= time_until <= window:
                subject = f"Reminder: {contest.get('event', 'Contest')} starts in ~{label}"
                body = (
                    f"Contest: {contest.get('event')}\n"
                    f"Resource: {contest.get('resource')}\n"
                    f"Starts at: {start.isoformat()}\n"
                    f"Link: {contest.get('href')}\n"
                )
                send_email(subject, body)
                entry[key] = True
                print(f"Sent {label} reminder for {contest.get('event')}")

        state[contest_id] = entry

    # Drop contests that are no longer in the upcoming list (started/removed)
    # to keep state.json from growing forever.
    state = {cid: v for cid, v in state.items() if cid in active_ids}
    save_state(state)


if __name__ == "__main__":
    main()
