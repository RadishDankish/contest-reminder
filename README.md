# Contest Reminder

Fetches upcoming contests from clist.by and emails you a reminder 24h and
6h before each one starts. Runs entirely on GitHub Actions' free tier —
no server needed.

## Setup

1. **Create a new GitHub repo** and push these files to it (keep `state.json`
   at the repo root — the workflow updates it in place, so it must stay
   tracked and start as `{}`).

2. **Get your clist.by API credentials**
   - Log in at https://clist.by/login/
   - Get your username and API key from https://clist.by/api/v4/doc/
     (your profile/API page shows both).

3. **Create a Gmail App Password** (used to send mail via SMTP)
   - Requires 2-Step Verification enabled on the Gmail account.
   - Go to https://myaccount.google.com/apppasswords and generate a
     16-character app password. Use that, not your normal Gmail password.

4. **Add repo secrets**
   Go to your repo → Settings → Secrets and variables → Actions → New
   repository secret, and add:
   - `CLIST_USERNAME` — your clist.by username
   - `CLIST_API_KEY` — your clist.by API key
   - `GMAIL_ADDRESS` — the Gmail address sending the reminder
   - `GMAIL_APP_PASSWORD` — the app password from step 3
   - `TO_EMAIL` — where reminders should be sent (can be the same as
     `GMAIL_ADDRESS`)

5. **(Optional) Restrict to specific judges**
   By default you'll get reminders for every contest clist.by tracks. To
   limit it, go to repo → Settings → Secrets and variables → Actions →
   Variables tab → New repository variable:
   - `CLIST_RESOURCES` — comma-separated resource names, e.g.
     `codeforces.com,leetcode.com,atcoder.jp`

6. **Enable the workflow**
   GitHub disables scheduled workflows on repos with no recent activity
   sometimes — if it doesn't seem to be running, go to the Actions tab and
   manually trigger it once via "Run workflow" (this also lets you test
   everything works before waiting on the cron).

## How it works

- Runs every 15 minutes via GitHub Actions cron.
- Fetches upcoming contests from `GET /api/v4/contest/` on clist.by.
- For each contest, checks whether time-until-start has just crossed the
  24h or 6h mark (within a 15-minute tolerance window, matching the cron
  interval).
- Sends an email via Gmail SMTP for any reminder that's newly due.
- Tracks which reminders have already been sent in `state.json`, which the
  workflow commits back to the repo after each run — this is what prevents
  duplicate emails across runs.
- Contests that are no longer in the "upcoming" list (i.e. they've started)
  are pruned from `state.json` automatically, so it doesn't grow forever.

## Notes / things to verify on first run

- clist.by's API may return contest start times under either `start` or
  `start_time` depending on API version — the script checks both, but
  worth confirming against a real response after your first run.
- Throttle limit on clist.by is 10 requests/minute; this script makes 1
  request per run, well within that.
- If you want tighter/looser reminder precision, adjust the cron schedule
  in `.github/workflows/reminder.yml` and the `TOLERANCE` value in
  `fetch_and_notify.py` together (they should roughly match).
