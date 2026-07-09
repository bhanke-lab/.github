#!/usr/bin/env python3
"""Rebuild the andon board. Rev C: self-monitoring, availability, sparklines, title block."""
import json
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone
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
    ".github": "This page, self monitor",
    "TENON": "Translator engine for native optimizer notation",
    "trimtab": "Price modeling for the right trim decisions",
    "paper-route": "Scheduled BI reports to dashboards",
    "notion-morning-print": "Automated printer from Notion database",
    "local-inventory-scanner": "Low cost offline inventory scanner",
    "garmin-notion": "Garmin data into training log",
    "intervals-to-notion": "Training data to for AI coach legibility",
    "intervals-icu-mcp": "Decommissioned",
}
HIDDEN = set()  # repo names to keep off the board entirely

LAMP = {"IN SERVICE": "#3fb950", "PM DUE": "#d29922", "DOWN": "#f85149"}
AVAIL_FLOOR = 75  # percent; below this a live repo goes PM DUE


def gh(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def status_of(repo, avail=None):
    if repo["archived"]:
        return "DOWN"
    if repo["open_issues_count"] > 0:
        return "PM DUE"
    if avail is not None and avail < AVAIL_FLOOR:
        return "PM DUE"
    return "IN SERVICE"


def recent_commits(repo, n=5):
    commits = gh("https://api.github.com/repos/" + ORG + "/" + repo["name"] + "/commits?per_page=" + str(n))
    out = []
    for item in commits:
        c = item["commit"]
        out.append((c["committer"]["date"], item["sha"][:7], c["message"].splitlines()[0]))
    return out


def availability(repo):
    """Success rate of the last 100 completed workflow runs. None if no runs."""
    try:
        data = gh("https://api.github.com/repos/" + ORG + "/" + repo["name"] + "/actions/runs?status=completed&per_page=100")
        runs = data.get("workflow_runs", [])
        if not runs:
            return None
        ok = sum(1 for r in runs if r["conclusion"] == "success")
        return 100.0 * ok / len(runs)
    except Exception:
        return None


def weekly_commits(repo):
    """Commit counts for the last 26 weeks. Empty if stats aren't computed yet."""
    try:
        data = gh("https://api.github.com/repos/" + ORG + "/" + repo["name"] + "/stats/participation")
        return data["all"][-26:]
    except Exception:
        return []


def clip(s, n):
    return s if len(s) <= n else s[: n - 3] + "..."


def build_svg(repos, extras, stamp, days, rev):
    row_h = 44
    top = 100
    width = 1160
    height = top + row_h * len(repos) + 96
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Andon board">',
        "<style>",
        "text { font-family: Consolas, 'Courier New', monospace; font-size: 17px; }",
        ".hd { fill: #8b949e; font-size: 14px; letter-spacing: 2px; }",
        ".name { fill: #e6edf3; }",
        ".dim { fill: #8b949e; }",
        ".st { font-size: 15px; letter-spacing: 1px; }",
        ".tb { fill: #8b949e; font-size: 12px; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="12" fill="#0d1117" stroke="#30363d"/>',
        '<text x="28" y="44" class="hd">LINE STATUS</text>',
        f'<text x="{width - 28}" y="44" class="hd" text-anchor="end">{ORG.upper()}</text>',
        f'<line x1="28" y1="64" x2="{width - 28}" y2="64" stroke="#30363d"/>',
    ]
    y = top
    for r in repos:
        avail, weeks = extras[r["name"]]
        st = status_of(r, avail)
        color = LAMP[st]
        steers = clip(STEERS.get(r["name"], r["description"] or ""), 44)
        pulse = "" if st == "IN SERVICE" else '<animate attributeName="opacity" values="0.25;0.8;0.25" dur="2s" repeatCount="indefinite"/>'
        parts += [
            f'<circle cx="40" cy="{y}" r="13" fill="{color}" opacity="0.25">{pulse}</circle>',
            f'<circle cx="40" cy="{y}" r="7" fill="{color}"/>',
            f'<text x="62" y="{y + 6}" class="name">{escape(clip(r["name"], 23))}</text>',
            f'<text x="300" y="{y + 6}" class="dim">{escape(steers)}</text>',
        ]
        if weeks:
            peak = max(weeks) or 1
            for i, n in enumerate(weeks):
                h = max(2, round(18 * n / peak)) if n else 1
                bx = 770 + i * 5
                parts.append(f'<rect x="{bx}" y="{y + 9 - h}" width="4" height="{h}" fill="{color}" opacity="0.7"/>')
        else:
            parts.append(f'<text x="770" y="{y + 6}" class="dim">no data</text>')
        am = "--" if avail is None else str(round(avail)) + "%"
        parts += [
            f'<text x="920" y="{y + 6}" class="st" fill="{color}">{st}</text>',
            f'<text x="{width - 28}" y="{y + 6}" class="dim" text-anchor="end">AVAIL {am}</text>',
        ]
        y += row_h
    div = y - 12
    foot = y + 20
    tb_x = width - 328
    parts += [
        f'<line x1="28" y1="{div}" x2="{width - 28}" y2="{div}" stroke="#30363d"/>',
        f'<text x="28" y="{foot}" class="dim">LAST INSPECTION {stamp}</text>',
        f'<text x="28" y="{foot + 26}" class="dim">DAYS SINCE THE LAST MANUAL PROCESS WAS ELIMINATED: {days}</text>',
        f'<rect x="{tb_x}" y="{div + 10}" width="300" height="72" fill="none" stroke="#30363d"/>',
        f'<line x1="{tb_x}" y1="{div + 34}" x2="{tb_x + 300}" y2="{div + 34}" stroke="#30363d"/>',
        f'<line x1="{tb_x}" y1="{div + 58}" x2="{tb_x + 300}" y2="{div + 58}" stroke="#30363d"/>',
        f'<line x1="{tb_x + 150}" y1="{div + 10}" x2="{tb_x + 150}" y2="{div + 82}" stroke="#30363d"/>',
        f'<text x="{tb_x + 8}" y="{div + 27}" class="tb">DRAWN BY: andon-bot</text>',
        f'<text x="{tb_x + 158}" y="{div + 27}" class="tb">REV: {rev}</text>',
        f'<text x="{tb_x + 8}" y="{div + 51}" class="tb">DATE: {stamp[:10]}</text>',
        f'<text x="{tb_x + 158}" y="{div + 51}" class="tb">SHEET 1 OF 1</text>',
        f'<text x="{tb_x + 8}" y="{div + 75}" class="tb">CHECKED BY: nobody</text>',
        f'<text x="{tb_x + 158}" y="{div + 75}" class="tb">SCALE: NTS</text>',
        "</svg>",
    ]
    return "\n".join(parts)


def main():
    repos = gh("https://api.github.com/orgs/" + ORG + "/repos?per_page=100&type=public")
    repos = [r for r in repos if r["name"] not in HIDDEN]
    order = {name: i for i, name in enumerate(STEERS)}
    repos.sort(key=lambda r: (r["archived"], order.get(r["name"], len(order)), r["name"].lower()))

    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d %H:%M UTC")
    rev = os.environ.get("GITHUB_SHA", "local")[:7]
    live = [r for r in repos if not r["archived"]]
    newest = max(r["created_at"] for r in live)
    born = datetime.fromisoformat(newest.replace("Z", "+00:00"))
    days = (now - born).days

    extras = {}
    for r in repos:
        extras[r["name"]] = (availability(r), weekly_commits(r))

    svg = build_svg(repos, extras, stamp, days, rev)
    with open(SVG_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)

    # Shift log: up to three commits per repo, twelve newest shown. Skip .github, it's all bot noise.
    cutoff = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    entries = []
    for r in repos:
        if r["name"] == ".github":
            continue
        try:
            for ts, sha, subject in recent_commits(r, 3):
                if r["archived"]:
                    sign = "-"
                elif ts[:10] >= cutoff:
                    sign = "+"
                else:
                    sign = " "
                entries.append((ts, sign, r["name"], sha, subject))
        except Exception:
            pass
    entries.sort(reverse=True)
    log = "\n".join(
        sign + " " + ts[:10] + "  " + sha + "  " + name + ": " + clip(subject, 48)
        for ts, sign, name, sha, subject in entries[:12]
    )
    log = "@@ -0,0 +1," + str(min(12, len(entries))) + " @@ shift log" + "\n" + log

    counts = {}
    for r in repos:
        st = status_of(r, extras[r["name"]][0])
        counts[st] = counts.get(st, 0) + 1
    alt = ", ".join(str(v) + " " + k.lower() for k, v in counts.items())

    cache_bust = now.strftime("%Y%m%d%H%M")
    board = "\n".join([
        START,
        "",
        "![Andon board: " + alt + "](" + SVG_URL + "?v=" + cache_bust + ")",
        "",
        "<details>",
        "<summary>shift log</summary>",
        "",
        FENCE + "diff",
        log,
        FENCE,
        "",
        "</details>",
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