# EEH Work Ledger: Claude Code Skill for Work Logs, Time Tracking and Timesheets

![CI tests on Windows and Linux](https://github.com/shubh-cloudops/eeh-work-ledger/actions/workflows/ci.yml/badge.svg) ![MIT license](https://img.shields.io/badge/license-MIT-blue.svg) ![Python 3 standard library](https://img.shields.io/badge/python-3-blue.svg)

**EEH Work Ledger is an open-source Claude Code skill that keeps a daily work log, tracks your time and builds timesheets and proof-of-work reports for IT employees.** It pulls evidence from Microsoft Teams, Outlook and Zoho Projects into one tamper-evident work ledger. It then generates HTML reports for performance appraisals, manager data requests and audits. Everything is consent-based: it tracks **your own** activity only and is not employee monitoring software.

Also on the Agensi marketplace: [EEH Work Ledger on Agensi](https://agensi.io/skills/eeh-work-ledger).

## Features

- **Daily work log in one line:** `l: standup 10:00-10:15 MTG <teams link>` adds a timestamped, evidence-linked entry.
- **Time tracking and timesheets:** end-of-day totals, gap detection and CSV timesheet export for Zoho Projects timelogs.
- **Tamper-evident audit trail:** an append-only Markdown ledger with a SHA-256 hash chain. `python eeh.py verify` flags edited rows.
- **Proof-of-work and appraisal reports:** professional HTML reports with a timeline, evidence links, hours by project and an integrity check.
- **Manager data requests:** a project manager, team lead or HR sends a request, and the report you share is logged with its hash.
- **Microsoft Teams, Outlook and Zoho Projects integration** through Claude MCP connectors.
- **Superpowers plugin support** for developers, DevOps, QA and SRE workflows.
- **Low token usage:** a Python script does the calculations and formatting, so Claude only writes short commands.

## How it works

```mermaid
flowchart LR
  T[Teams / Outlook<br/>Microsoft 365 connector] --> C
  Z[Zoho Projects connector] --> C
  S[Superpowers milestones<br/>spec, plan, tests, PR] --> C
  C[Claude Code<br/>CLAUDE.md + 2 skills] -->|one-line command| P[eeh.py]
  P --> L[(work-ledger.md<br/>append-only, hash-chained)]
  L --> R[HTML report / CSV timesheet]
  M[Manager request] -->|req| P
  R -->|employee approves| M
```

## Sample report

![Sample proof-of-work HTML report: hours by project, timeline with evidence links and integrity check](docs/report.png)

## Design decisions

| Decision | Why | Alternative considered |
|---|---|---|
| Markdown ledger, not a database | Readable by anyone, diff-able, no server to run | SQLite: faster queries, but not human-readable |
| SHA-256 hash chain per row | Any edit to a past row is detectable with `verify` | Signed commits / WORM storage: stronger, needs infra |
| Script writes reports, not the model | Deterministic output and near-zero tokens | Model-written reports: flexible, costly, can drift |
| Own data only, consent-based | Legal and ethical; evidence stays admissible | Org-wide monitoring tools (Hubstaff, Teramind) |
| Python stdlib only | Runs on any Windows/Linux box with no installs | Click/Rich: nicer CLI, extra dependencies |
| CI on Windows and Linux | Proves it works where employees actually run it | Linux only: misses path/encoding issues |

## What's in the kit

| File | Job | Loaded into context |
|---|---|---|
| `CLAUDE.md` | Profile, rules, token budget, Superpowers bridge, shortcuts | Always (~450 tokens) |
| `.claude/skills/eeh-ledger/SKILL.md` | Start day, log, end day, timesheet | Only when triggered |
| `.claude/skills/eeh-report/SKILL.md` | Proof, manager data requests, appraisal | Only when triggered |
| `eeh.py` | Writes the ledger, hash chain, totals, gaps, HTML report, CSV timesheet | Never (runs outside the model) |
| `work-ledger.md` | **The single file holding all your data** (created by `init`) | Only the slices you ask for |
| `request-template.md` | Form a PM/lead/HR sends you to request data | No |
| `examples/` | Sample ledger and a sample appraisal report (fictional data) | No |
| `tests/`, `.github/workflows/ci.yml` | Unit tests run on Windows and Linux on every push | No |

Why: Claude Code is used rather than claude.ai chat because a ledger file needs a real folder, and Superpowers only runs in Claude Code.

## How the pieces fit

1. **Doing the work:** Superpowers (technical roles) gives Claude a disciplined method: brainstorm, plan, test-first, verify, review.
2. **Proving the work:** each Superpowers milestone adds one ledger row with its artefact (spec, plan, test output, PR). Teams/Outlook/Zoho add meeting, message and task evidence at end of day.
3. **Sharing the proof:** a manager sends the request form, you run `req`, and `eeh.py` generates the report and logs that you shared it, along with the report's hash.

## Token plan

| Saving | How |
|---|---|
| Always-on prompt 73% smaller | v1 prompt was 1,209 words; `CLAUDE.md` is 328. The details live in skills, which load only when you use them |
| 3 skills merged into 2 | Fewer skill descriptions in every session |
| No model-written tables | `eeh.py` does the maths, hashing and HTML. Claude writes a one-line command |
| No whole-ledger reads | `eeh.py show --from --to` returns only the rows needed |
| One connector pass a day | At end day only: today's items, your own, max 25 |
| Fresh session daily | The ledger holds the memory, so long chats don't keep getting re-read |
| Cheaper model for logging | `/model sonnet` or `haiku` for `l:` and `ed` |
| Superpowers kept lean | `executing-plans` over `subagent-driven-development`; skip brainstorming under 30 min |

Advanced option: a scheduled end-of-day routine that runs `ed` automatically.

## Superpowers by role

| Role | Install? | Most useful Superpowers skills |
|---|---|---|
| Developer, DevOps, Cloud, SRE | Yes | writing-plans, test-driven-development, systematic-debugging, verification-before-completion, finishing-a-development-branch |
| QA / Automation | Yes | test-driven-development, systematic-debugging, requesting-code-review |
| L1/L2 Support | Optional | systematic-debugging |
| Lead, PM, Manager, Architect | Optional | brainstorming, writing-plans (they work for non-code plans too) |

Superpowers costs about 800 tokens per session for its always-on `using-superpowers` instructions. Other skills load on demand. Source: github.com/obra/superpowers (MIT).

## Setup (Windows 11, PowerShell)

1. **Install Python and Git.**
   ```powershell
   winget install -e --id Python.Python.3.12
   winget install -e --id Git.Git
   ```
   Close and reopen PowerShell, then run `python --version`.
   Expected result: `Python 3.12.x`.
   Fix: if `python` opens the Microsoft Store, go to Settings > Apps > Advanced app settings > App execution aliases and turn off both Python aliases.

2. **Install Claude Code.** This needs a paid Claude plan (Pro or above). If you already have one, it costs nothing extra.
   ```powershell
   irm https://claude.ai/install.ps1 | iex
   ```
   Expected result: `claude --version` prints a version. You can also use the Code tab in the Claude desktop app.

3. **Create the ledger folder in your company OneDrive and copy the kit into it.**
   ```powershell
   mkdir "$env:OneDrive\EEH"
   cd "$env:OneDrive\EEH"
   ```
   Copy `CLAUDE.md`, `eeh.py`, `request-template.md` and the `.claude` folder into it.
   Expected result: `dir -Force` lists all four.
   Why: company OneDrive keeps the evidence inside approved storage and gives it file version history.

4. **Create your ledger.**
   ```powershell
   python eeh.py init --name "Your Name" --designation "DevOps Engineer" --level L2 --team "Cloud Ops" --hours 09:30-18:30
   ```
   Expected result: `Created work-ledger.md`.

5. **Fill the Profile line** at the top of `CLAUDE.md` (replace each `{{…}}`).

6. **Connect Microsoft 365 (Teams, Outlook) and Zoho Projects** at claude.ai > Settings > Connectors. Then run `claude` in the folder and type `/mcp`.
   Expected result: both connectors are listed.
   Fix: if your company blocks Microsoft 365, ask IT to approve the Claude app in Entra ID. Until then, paste links in by hand; those rows are marked `manual`.

7. **Optional, for technical roles: install Superpowers.** Inside `claude`:
   ```
   /plugin install superpowers@claude-plugins-official
   ```
   Expected result: `/plugin` lists superpowers as enabled.

8. **Test drive.** Inside `claude`, type: `sd`, then `l: standup 10:00-10:15 MTG <teams link>`, then `ed`.
   Expected result: a one-line `E0001 …` confirmation, then a close summary with totals, gaps and a seal hash.

## For managers: requesting data

Send the employee the block in `request-template.md`. The employee types `req <who> <from..to> <purpose>`. The employee then gets an HTML report to review and send you. The report includes hours, a timeline with evidence links, gaps, and an integrity check. The request and the share are both recorded in their ledger.

## Teardown

1. Inside `claude`: `/plugin uninstall superpowers`.
2. claude.ai > Settings > Connectors: disconnect Microsoft 365 and Zoho Projects.
3. Delete `CLAUDE.md`, `eeh.py` and `.claude` from the folder. Keep or delete `work-ledger.md` and reports according to company retention policy.
4. Optional: `winget uninstall Python.Python.3.12`.

## FAQ

**What is EEH Work Ledger?**
It's a Claude Code skill and a Python script that together keep a verifiable work log, track your time and generate timesheets and work reports for IT employees.

**Is it employee monitoring software?**
No. It tracks only your own activity, with your consent, and never collects colleagues' data. It is a personal work-evidence tool, not workplace surveillance.

**Does it work with Microsoft Teams and Zoho?**
Yes. It reads your own Teams messages and meetings and your Outlook mail through the Microsoft 365 connector, and your Zoho Projects tasks and timelogs through the Zoho Projects connector.

**Can my manager verify the report?**
Yes. Each report has a SHA-256 hash that is also recorded in your ledger. `python eeh.py verify` shows whether any ledger row was changed after it was written.

**Does it run on Windows?**
Yes. It needs only Python 3 and its standard library, and CI tests it on Windows and Linux on every push.

**How much does it cost?**
The kit is free and MIT-licensed. You need a Claude plan that includes Claude Code.

