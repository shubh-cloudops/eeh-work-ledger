---
name: eeh-report
description: Proof, data requests from managers, and appraisal reports from the work ledger; use on prove, req, appraisal, or when someone asks for my work data.
---

# EEH Report

Reports are built by `python eeh.py report`, not written by Claude. Claude only adds a short covering note.

## req <who> <from..to> <purpose>  (a manager, PM, lead or HR asks for data)
1. Log it first: `python eeh.py req --by "<role (name)>" --from D --to D --project P --purpose "..." --due D --evidence <request link> --src teams|outlook`
2. Check the scope is minimal: only the period and project asked for. If the request is broader than its purpose, suggest a narrower scope (A) as asked B) narrow to project (recommended when the purpose is project-specific) C) Other).
3. `python eeh.py report --req R0001 --out report-R0001.html` (this also logs a `share` row with the report hash).
4. Draft a ≤4-line reply to the requester naming the period, hours, evidence %, and the report hash. Share only on Yes.

## prove <claim>
1. `python eeh.py show --from D --to D --project P` for the slice only.
2. If rows are low confidence, do one targeted connector search (Teams/Outlook/Zoho) for that ref and date, and add any found link with `fix --evidence`.
3. Answer in this shape: Claim (1 line) · Evidence rows (IDs + links) · Approvals received (exact quote ≤25 words + link) · Gaps (honest) · Suggested reply (≤4 lines).
4. If the evidence contradicts the claim, say so plainly.

## appraisal <from..to>
`python eeh.py report --from D --to D --out appraisal.html`, then a ≤8-line achievement summary grouped by project, each line citing ledger IDs.

## Rules
- Quote other people's instructions word for word with a link; never paraphrase them.
- Leave out colleagues' unrelated messages and any personal data.
- Confidential or customer content is referenced by ID, never copied.
