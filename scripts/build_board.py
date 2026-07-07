#!/usr/bin/env python3
"""Rebuild the andon board SVG and shift log in profile/README.md. Stdlib only."""
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

ORG = "bhanke-lab"
HERE = os.path.dirname(os.path.abspath(__file__))
README = os.path.join(HERE, "..", "profile", "README.md")
SVG_PATH = os.path.join(HERE, "..", "profile", "board.svg")
SVG_URL = "https://raw.githubusercontent.com/bhanke-lab/.github/main/profile/board.svg"
START = "<!-- BOARD:START -->"
END = "<!-- BOARD:END -->"
FENCE = "`" * 3

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

LAMP = {
    "IN SERVICE": "#3fb950",
    "PM DUE": "#d29922",
    "DOWN": "#f85149",
}


def gh(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def status_of(repo):
    if repo["archived"]:
        return "DOWN"
    if repo["open_issues_count"] > 0:
        return "PM DUE"
    return "IN SERVICE"


def latest_commit(repo):
    commits = gh("https://api.github.com/repos/" + ORG + "/" + repo["name"] + "/commits?per_page=1")
    c = commits[0]["commit"]
    return c["committer"]["date"][:10], c["message"].splitlines()[0]


def clip(s, n):
    return s if len(s) <= n else s[: n - 3] + "..."


def build_svg(repos, stamp, days):
    row_h = 34
    top = 78
    width = 900
    height = top + row_h * len(repos) + 40
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Andon board">',
        "<style>",
        "text { font-family: Consolas, 'Courier New', monospace; font-size: 13px; }",
        ".hd { fill: #8b949e; font-size: 12px; letter-spacing: 2px; }",
        ".name { fill: #e6edf3; }",
        ".dim { fill: #8b949e; }",
        ".st { font-size: 12px; letter-spacing: 1px; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="12" fill="#0d1117" stroke="#30363d"/>',
        '<text x="28" y="40" class="hd">LINE STATUS</text>',
        f'<text x="{width - 28}" y="40" class="hd" text-anchor="end">{ORG.upper()}</text>',
        f'<line x1="28" y1="56" x2="{width - 28}" y2="56" stroke="#30363d"/>',
    ]
    y = top
    for r in repos:
        st = status_of(r)
        color = LAMP[st]
        steers = clip(STEERS.get(r["name"], r["description"] or ""), 40)
        parts += [
            f'<circle cx="40" cy="{y}" r="10" fill="{color}" opacity="0.25"/>',
            f'<circle cx="40" cy="{y}" r="5" fill="{color}"/>',
            f'<text x="62" y="{y + 5}" class="name">{escape(r["name"])}</text>',
            f'<text x="320" y="{y + 5}" class="dim">{escape(steers)}</text>',
            f'<text x="640" y="{y + 5}" class="st" fill="{color}">{st}</text>',
            f'<text x="{width - 28}" y="{y + 5}" class="dim" text-anchor="end">{(r["pushed_at"] or "")[:10]}</text>',
        ]
        y += row_h
    div = y - 10
    foot = y + 18
    parts += [
        f'<line x1="28" y1="{div}" x2="{width - 28}" y2="{div}" stroke="#30363d"/>',
        f'<text x="28" y="{foot}" class="dim">LAST INSPECTION {stamp}</text>',
        f'<text x="{width - 28}" y="{foot}" class="dim" text-anchor="end">DAYS SINCE THE LAST MANUAL PROCESS WAS ELIMINATED: {days}</text>',
        "</svg>",
    ]
    return "\n".join(parts)


def main():
    repos = gh("https://api.github.com/orgs/" + ORG + "/repos?per_page=100&type=public")
    repos = [r for r in repos if r["name"] not in HIDDEN and r["name"] != ".github"]
    repos.sort(key=lambda r: (r["archived"], r["name"].lower()))

    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d %H:%M UTC")
    live = [r for r in repos if not r["archived"]]
    newest = max(r["created_at"] for r in live)
    born = datetime.fromisoformat(newest.replace("Z", "+00:00"))
    days = (now - born).days

    svg = build_svg(repos, stamp, days)
    with open(SVG_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)

    # Shift log: newest commit per repo, six most recent lines.
    entries = []
    for r in repos:
        try:
            date, subject = latest_commit(r)
        except Exception:
            date, subject = (r["pushed_at"] or "")[:10], "no commit data"
        sign = "-" if r["archived"] else "+"
        entries.append((date, sign, r["name"], subject))
    entries.sort(reverse=True)
    log = "\n".join(
        sign + " " + date + "  " + name + ": " + clip(subject, 58)
        for date, sign, name, subject in entries[:6]
    )

    counts = {}
    for r in repos:
        st = status_of(r)
        counts[st] = counts.get(st, 0) + 1
    alt = ", ".join(str(v) + " " + k.lower() for k, v in counts.items())

    cache_bust = now.strftime("%Y%m%d%H%M")
    board = "\n".join([
        START,
        "",
        "![Andon board: " + alt + "](" + SVG_URL + "?v=" + cache_bust + ")",
        "",
        FENCE + "diff",
        log,
        FENCE,
        "",
        END,
    ])

    with open(README, encoding="utf-8") as f:
        text = f.read()
    pattern = re.compile(re.escape(START) + ".*?" + re.escape(END), re.DOTALL)
    new = pattern.sub(board, text)
    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    print("Board updated.")


if __name__ == "__main__":
    main()