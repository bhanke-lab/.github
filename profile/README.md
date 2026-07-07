# "CALL ME TRIMTAB" - BUCKY

A trim tab is the small rudder bolted to the trailing edge of a ship's big rudder. The big rudder is too heavy to push directly, so you turn the small one. Deflecting the tab generates lift on the tab. That lift is small, but it acts at the trailing edge, the longest moment arm available on the rudder. This produces enough torque about the rudder stock to rotate the whole thing. The rudder then generates the turning force on the hull.

Nobody hands you the wheel on any big systems, and most of them can't be easily replaced. But they all have a trailing edge.

Every repo here is a trim tab. Small tools, built for zero dollars a month, that push on one surface of a big system.

Below is the shop floor. The board updates automatically.

## Line status

<!-- BOARD:START -->

![Andon board: 6 in service](https://raw.githubusercontent.com/bhanke-lab/.github/main/profile/board.svg?v=202607072008)

```diff
+ 2026-07-07  TENON: Update README with logo, images, formatting changes, qu...
+ 2026-07-01  trimtab: Revise README for clarity on trim decisions and tools
+ 2026-06-30  paper-route: Add PolyForm Noncommercial License 1.0.0
+ 2026-06-30  notion-morning-print: Add PolyForm Noncommercial License 1.0.0
+ 2026-06-30  local-inventory-scanner: Create LICENSE.md
+ 2026-06-25  garmin-notion: add troubleshooting section to README to help debug sta...
```

<!-- BOARD:END -->

IN SERVICE means it runs in production somewhere. PM DUE means open issues or something waiting on me. DOWN means decommissioned on purpose.

## Work order history

Every tool here exists because something broke. The tickets are closed but kept on file.

### WO-0001: [fiix-analytics-auto-downloader](https://github.com/bhanke-lab/fiix-analytics-auto-downloader)

- Symptom: the morning CMMS analytics report required a person to log in and download it, every day, before 7 AM.
- Root cause: Looker delivers scheduled reports to email and nowhere else.
- Corrective action: PowerShell over raw IMAP/TLS. Finds the day's report email, parses the MIME by hand, decodes the PDF, drops it on the shared drive with a dated filename. Retries for an hour if the report is late.
- Parts: PowerShell 5.1, SslStream, Task Scheduler. No modules.
- Surface pushed: one inbox.

### WO-0002: [local-inventory-scanner](https://github.com/bhanke-lab/local-inventory-scanner)

- Symptom: parts left the parts room with no record of who took what.
- Root cause: checkout meant typing on a keyboard, and nobody types with greasy gloves at 5 AM.
- Corrective action: scan a badge, then scan parts. Excel does the rest. It strips the scanner's wake-up garbage, tells a badge from a part, looks up the tech, carries their identity for five minutes of scans, and logs every line with a timestamp.
- Parts: a $40 Bluetooth scanner, a tablet, Excel formulas. No code at all.
- Surface pushed: one spreadsheet.

### WO-0003: [TENON](https://github.com/bhanke-lab/TENON)

- Symptom: every sawing order got translated into the trimmer optimizer's product list by hand, and hands make mistakes.
- Root cause: the order system and the optimizer don't speak the same language, and no vendor was going to teach them.
- Corrective action: a translator. Reads the order, writes the Active Products list. The ruleset lives in one YAML file so it grows one edge case at a time. Currently 95.1% recall and 90.2% precision across 45 fixtures and 10 species.
- Parts: Python, one YAML file.
- Surface pushed: one config screen.

### WO-0004: [paper-route](https://github.com/bhanke-lab/paper-route)

- Symptom: the shift-turnover report needed a human to carry a PDF from an inbox to a TV, daily.
- Root cause: no path between a scheduled BI email and a screen.
- Corrective action: two scripts. One pulls the newest report PDF out of the inbox over raw IMAP. The other watches that folder and throws the newest PDF fullscreen on the wall in kiosk mode.
- Parts: PowerShell 5.1+, Edge. Nothing else.
- Surface pushed: one inbox and one wall.

### WO-0005: [notion-morning-print](https://github.com/bhanke-lab/notion-morning-print)

- Symptom: the day's task list lived in a browser tab, and mornings started without it.
- Root cause: screens lose to paper before 7 AM.
- Corrective action: a script that pulls today's tasks out of Notion, ranks them, and sends them to the office printer on a schedule. There's a checkbox at the bottom reminding you to go close them out at the end of the day.
- Parts: Python, Task Scheduler, one office printer.
- Surface pushed: one sheet of paper.

### WO-0006: [trimtab](https://github.com/bhanke-lab/trimtab)

- Symptom: trim decisions on the line got argued from gut feel, because nobody could see what a board was actually worth.
- Root cause: the value math existed only inside the optimizer, where nobody can watch it think.
- Corrective action: three tools. An Excel value table that shows what any board is worth at any length, with a one-button reset. A Python pricing model that builds the full price grid and decision matrix from the optimizer's own export, with the protections baked into the prices themselves. A sim comparison sheet that shows what a policy change does before it runs.
- Parts: Excel, Power Query, Office Scripts, Python.
- Surface pushed: the price grid, which is the only thing the machine actually listens to.

### WO-0007: [garmin-notion](https://github.com/bhanke-lab/garmin-notion)

- Symptom: years of training data locked in a watch vendor's app.
- Root cause: vendors don't export to where you actually live.
- Corrective action: a scheduled sync that mirrors activities and sleep into Notion databases, where they can be queried next to everything else.
- Parts: Python, GitHub Actions.
- Surface pushed: one cron schedule.

### WO-0008: intervals-icu-mcp (closed, superseded)

- Symptom: my AI coach couldn't see my training data.
- Root cause: the data sat in Intervals.icu and the coach lives in Notion.
- Corrective action: a full MCP server on a cloud VM. It worked. It also needed a server and a bill for what a cron could do free. Decommissioned and superseded by WO-0009.
- Parts: TypeScript, a small VM, a lesson.
- Surface pushed: mostly my own assumptions.

### WO-0009: [intervals-to-notion](https://github.com/bhanke-lab/intervals-to-notion)

- Symptom: same as WO-0008.
- Root cause: same as WO-0008.
- Corrective action: the trim tab version. A Python sync that mirrors activities and wellness into Notion four times a day and links each workout to its planned session. Low readiness gets flagged before I have to ask why a run felt bad. Three-year backfill, idempotent, survives timeouts.
- Parts: Python, GitHub Actions cron. Zero dollars a month.
- Surface pushed: one cron schedule.

## Colophon

This page is a trim tab too. A Python script with no dependencies and a free cron rebuild the board every morning, then mirror this one file to my personal profile. One small file steers two landing pages.
