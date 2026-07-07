#!/usr/bin/env python3
"""Rebuild the andon board in profile/README.md. Stdlib only, no pip installs."""
import json
import os
import re
import urllib.request
from datetime import datetime, timezone

ORG = "bhanke-lab"
README = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profile", "README.md")
START = "<!-- BOARD:START -->"
END = "<!-- BOARD:END -->"

# One-line "Steers" text per repo. Anything not listed falls back to its GitHub description.
STEERS = {
    "fiix-analytics-auto-downloader": "Daily CMMS reports onto the shared drive",
    "garmin-notion": "Watch data into my training log",
    "intervals-to-notion": "Training data to where my coach can read it",
    "local-inventory-scanner": "Who took what from the parts room",
    "notion-morning-print": "The first ten minutes of my morning",
    "paper-route": "Scheduled BI reports onto a wall-mounted TV",
    "TENON": "Sawing orders into TrimExpert product lists",
    "trimtab": "What the trimmer decides a board is worth",
    "intervals-icu-mcp": "Nothing anymore. Decommissioned.",
}
HIDDEN = set()  # repo names to keep off the board entirely


def gh(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def status_of(repo):
    if repo["archived"]:
        return "🔴 DOWN"
    if repo["open_issues_count"] > 0:
        return "🟡 PM DUE"
    return "🟢 IN SERVICE"


def main():
    repos = gh("https://api.github.com/orgs/" + ORG + "/repos?per_page=100&type=public")
    repos = [r for r in repos if r["name"] not in HIDDEN and r["name"] != ".github"]
    repos.sort(key=lambda r: (r["archived"], r["name"].lower()))

    rows = [
        "| Asset | Steers | Status | Last service |",
        "| --- | --- | --- | --- |",
    ]
    for r in repos:
        steers = STEERS.get(r["name"], r["description"] or "")
        last = (r["pushed_at"] or "")[:10]
        rows.append(
            "| [" + r["name"] + "](" + r["html_url"] + ") | " + steers + " | " + status_of(r) + " | " + last + " |"
        )

    live = [r for r in repos if not r["archived"]]
    newest = max(r["created_at"] for r in live)
    born = datetime.fromisoformat(newest.replace("Z", "+00:00"))
    days = (datetime.now(timezone.utc) - born).days
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    board = "\n".join(
        [START, "", *rows, "", "Last inspection: " + stamp, "", "Days since the last manual process was eliminated: " + str(days), END]
    )

    with open(README, encoding="utf-8") as f:
        text = f.read()
    pattern = re.compile(re.escape(START) + ".*?" + re.escape(END), re.DOTALL)
    new = pattern.sub(board, text)
    if new != text:
        with open(README, "w", encoding="utf-8", newline="\n") as f:
            f.write(new)
        print("Board updated.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()