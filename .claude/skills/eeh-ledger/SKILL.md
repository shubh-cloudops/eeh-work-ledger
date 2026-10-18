---
name: eeh-ledger
description: Daily work ledger and timesheet via eeh.py; use on sd/start day, l:/log, switch, ed/end day, ts/timesheet.
---

# EEH Ledger

All writes go through `python eeh.py` in the ledger folder. Print only its one-line result. Never hand-edit `work-ledger.md`.

## sd (start day)
1. If connected: today's Outlook calendar + my open Zoho Projects tasks (max 25).
2. Reply with a plan in ≤6 lines (time blocks, meetings fixed, one buffer). No ledger row yet.

## l: <what> [hh:mm-hh:mm | Nm] [ref] [link]
`python eeh.py add --start S --end E --project P --ref R --type T --detail "D" --evidence URL --src S`
- type: build, fix, review, meeting, support, docs, learning, admin, blocked, travel
- src: teams, outlook, zoho, git, ticket, manual. conf is auto (link + system source = high).
- Missing ref → ask once: A) link a task (recommended) B) log untracked C) Other.
- Wrong row → `python eeh.py fix --of E0007 --detail "..."` (never edit).

## ed (end day)
1. One connector pass for today only: Teams messages I sent + meetings attended, Outlook mails sent, Zoho tasks I updated. Add only items missing from `python eeh.py show`.
2. `python eeh.py close` → totals, gaps, low-confidence count, and a close hash.
3. Ask a reason for each gap (A) break B) unlogged work → log it C) leave as gap). Never guess.
4. Draft a 3–5 bullet EOD update that ends with `Ledger seal: <close-row hash>`. The posted message timestamps the seal outside the file. Send only on Yes.

## ts (timesheet)
1. Range: A) this week (recommended) B) last week C) custom D) Other.
2. `python eeh.py timesheet --from D --to D --out timesheet.csv` (15-min rounding by default).
3. Show totals and gaps from the close rows. Create Zoho Projects timelogs only on Yes, then log the timelog IDs with `fix` rows pointing at each entry.
