# Work & Evidence Data Request

Send this to the employee in Teams or Outlook. The link to this message becomes the request's evidence.

```
EEH data request
Requested by: <role> (<name>)
Period: <YYYY-MM-DD> to <YYYY-MM-DD>
Project / scope: <project or "all">
Purpose: <appraisal | status verification | client billing | audit | other>
Needed by: <YYYY-MM-DD>
Format: HTML report (default) | timesheet CSV
```

What you get back: an HTML report (summary, hours by project and activity, timeline with evidence links, daily gaps, integrity check) and its SHA-256. The same hash is recorded in the employee's ledger as a `share` row, and `python eeh.py verify` shows whether any ledger row was edited later.
