#!/usr/bin/env python3
"""EEH work ledger: one append-only, hash-chained Markdown file + reports.

Claude calls this with one short command instead of writing tables itself,
so arithmetic, hashing and report layout cost zero model tokens.
Standard library only. Run: python eeh.py <command> -h
"""
import argparse, csv, datetime as dt, hashlib, html, os, sys
from collections import defaultdict

LEDGER = os.environ.get("EEH_LEDGER", "work-ledger.md")
COLS = ["id", "kind", "date", "start", "end", "min", "project", "ref",
        "type", "detail", "evidence", "src", "conf", "hash"]
KINDS = {"work", "req", "share", "fix", "close"}


# ---------- storage ----------
def clean(v):
    return str(v or "").replace("|", "/").replace("\n", " ").strip()


def rows():
    if not os.path.exists(LEDGER):
        sys.exit(f"No ledger at {LEDGER}. Run: python eeh.py init ...")
    out = []
    with open(LEDGER, encoding="utf-8") as f:
        for line in f:
            if line.startswith("| ") and not line.startswith("| id ") and "---" not in line[:6]:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) == len(COLS):
                    out.append(dict(zip(COLS, cells)))
    return out


def header():
    meta = {}
    with open(LEDGER, encoding="utf-8") as f:
        for line in f:
            if line.startswith("- **"):
                k, _, v = line[4:].partition(":**")
                meta[k.strip()] = v.strip()
    return meta


def row_hash(prev, r):
    body = prev + "|" + "|".join(r[c] for c in COLS[:-1])
    return hashlib.sha256(body.encode()).hexdigest()[:16]


def append(r):
    existing = rows()
    prefix = {"work": "E", "req": "R", "share": "S", "fix": "F", "close": "C"}[r["kind"]]
    r["id"] = f"{prefix}{sum(1 for x in existing if x['id'][0] == prefix) + 1:04d}"
    for c in COLS[:-1]:
        r[c] = clean(r.get(c))
    r["hash"] = row_hash(existing[-1]["hash"] if existing else "genesis", r)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write("| " + " | ".join(r[c] for c in COLS) + " |\n")
    return r


def mins(start, end):
    if not (start and end):
        return 0
    a, b = (dt.datetime.strptime(t, "%H:%M") for t in (start, end))
    return int((b - a).total_seconds() // 60) % 1440


def in_range(r, a, b, project=None):
    return a <= r["date"] <= b and (not project or r["project"].lower() == project.lower())


# ---------- commands ----------
def cmd_init(a):
    if os.path.exists(LEDGER):
        sys.exit(f"{LEDGER} already exists; refusing to overwrite.")
    with open(LEDGER, "w", encoding="utf-8") as f:
        f.write(f"# Work Ledger\n\n"
                f"- **Owner:** {a.name}\n- **Designation:** {a.designation}\n"
                f"- **Level:** {a.level}\n- **Team:** {a.team}\n"
                f"- **Hours:** {a.hours}\n- **Created:** {dt.date.today()}\n\n"
                "Append-only. Never edit or delete a row: add a `fix` row. "
                "Integrity check: `python eeh.py verify`.\n\n"
                "Kinds: work = activity, req = data request received, share = data shared for a request, "
                "fix = correction, close = end-of-day seal.\n\n## Entries\n\n"
                "| " + " | ".join(COLS) + " |\n|" + "---|" * len(COLS) + "\n")
    print(f"Created {LEDGER}")


def cmd_add(a):
    m = a.min if a.min is not None else mins(a.start, a.end)
    r = append(dict(kind="work", date=a.date, start=a.start, end=a.end, min=m,
                    project=a.project, ref=a.ref, type=a.type, detail=a.detail,
                    evidence=a.evidence, src=a.src,
                    conf=a.conf or ("high" if a.evidence and a.src != "manual" else "medium" if a.evidence else "low")))
    print(f"{r['id']} {r['date']} {r['min']}m {r['project']} {r['conf']}")


def cmd_fix(a):
    r = append(dict(kind="fix", date=dt.date.today().isoformat(), ref=a.of,
                    detail=a.detail, evidence=a.evidence, src="manual", conf="-"))
    print(f"{r['id']} corrects {a.of}")


def gaps_for(day, work, hours):
    start, end = hours.split("-")
    spans = sorted((x["start"], x["end"]) for x in work if x["start"] and x["end"])
    cur, out = start, []
    for s, e in spans:
        if s > cur and mins(cur, s) > 15:
            out.append((cur, s, mins(cur, s)))
        cur = max(cur, e)
    if end > cur and mins(cur, end) > 15:
        out.append((cur, end, mins(cur, end)))
    return out


def cmd_close(a):
    all_rows = rows()
    if any(x["kind"] == "close" and x["date"] == a.date for x in all_rows):
        sys.exit(f"{a.date} is already closed. Log late items with add, then fix --of <close id>.")
    work = [x for x in all_rows if x["kind"] == "work" and x["date"] == a.date]
    total = sum(int(x["min"] or 0) for x in work)
    byp = defaultdict(int)
    for x in work:
        byp[x["project"] or "-"] += int(x["min"] or 0)
    gaps = gaps_for(a.date, work, header().get("Hours", "09:30-18:30"))
    low = sum(1 for x in work if x["conf"] == "low")
    summary = "; ".join(f"{p} {m}m" for p, m in byp.items())
    gap_txt = ", ".join(f"{s}-{e}" for s, e, _ in gaps) or "none"
    r = append(dict(kind="close", date=a.date, min=total, detail=f"{summary}; gaps {gap_txt}; low-conf {low}",
                    src="eeh", conf="-"))
    print(f"{r['id']} {a.date} total {total}m | {summary or 'no work rows'} | gaps {gap_txt} | low-conf {low} | seal {r['hash']}")


def cmd_show(a):
    for x in rows():
        if in_range(x, a.frm, a.to, a.project) and (not a.kind or x["kind"] == a.kind):
            print(" | ".join(x[c] for c in COLS[:-1] if x[c]))


def cmd_req(a):
    r = append(dict(kind="req", date=dt.date.today().isoformat(), project=a.project,
                    ref=f"{a.frm}..{a.to}", type=a.by, detail=f"{a.purpose}; due {a.due}",
                    evidence=a.evidence, src=a.src, conf="-"))
    print(f"{r['id']} logged request from {a.by} for {a.frm}..{a.to}")


def cmd_verify(_a):
    prev, bad = "genesis", []
    for x in rows():
        if row_hash(prev, x) != x["hash"]:
            bad.append(x["id"])
        prev = x["hash"]
    print("OK: chain intact" if not bad else f"TAMPERED or edited rows: {', '.join(bad)}")
    return not bad


def cmd_timesheet(a):
    agg = defaultdict(int)
    for x in rows():
        if x["kind"] == "work" and in_range(x, a.frm, a.to, a.project):
            agg[(x["date"], x["project"], x["ref"])] += int(x["min"] or 0)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "project", "task_ref", "hours"])
        for (d, p, ref), m in sorted(agg.items()):
            w.writerow([d, p, ref, round(round(m / a.round) * a.round / 60, 2)])
    print(f"Wrote {a.out}: {len(agg)} lines, {sum(agg.values()) / 60:.2f} h")


def cmd_report(a):
    allr = rows()
    meta = header()
    req = next((x for x in allr if x["id"] == a.req), None) if a.req else None
    if a.req and not req:
        sys.exit(f"No request {a.req}")
    if req:
        a.frm, a.to = req["ref"].split("..")
        a.project = a.project or req["project"] or None
    fixes = {x["ref"]: x["detail"] for x in allr if x["kind"] == "fix"}
    work = [x for x in allr if x["kind"] == "work" and in_range(x, a.frm, a.to, a.project)]
    closes = [x for x in allr if x["kind"] == "close" and in_range(x, a.frm, a.to)]
    total = sum(int(x["min"] or 0) for x in work)
    byp, byt = defaultdict(int), defaultdict(int)
    for x in work:
        byp[x["project"] or "-"] += int(x["min"] or 0)
        byt[x["type"] or "-"] += int(x["min"] or 0)
    ev = sum(1 for x in work if x["evidence"])
    high = sum(1 for x in work if x["conf"] == "high")
    chain_ok = cmd_verify(None)
    e = html.escape

    def table(head, body):
        return ("<table><tr>" + "".join(f"<th>{e(h)}</th>" for h in head) + "</tr>"
                + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in body) + "</table>")

    def link(v):
        return " ".join(f'<a href="{e(t)}">{e(t)}</a>' if t.startswith("http") else e(t) for t in v.split())

    timeline = [[e(x["date"]), e(f"{x['start']}-{x['end']}" if x["start"] else "-"), e(x["min"]),
                 e(x["project"]), e(x["ref"]), e(x["type"]),
                 e(x["detail"]) + (f"<br><em>Correction: {e(fixes[x['id']])}</em>" if x["id"] in fixes else ""),
                 link(x["evidence"]), e(x["conf"]), e(x["id"])] for x in work]
    title = f"Work &amp; Evidence Report: {e(meta.get('Owner', ''))}"
    req_html = (f"<p><b>Requested by:</b> {e(req['type'])} &nbsp; <b>Purpose:</b> {e(req['detail'])} "
                f"&nbsp; <b>Request ref:</b> {e(req['id'])} {link(req['evidence'])}</p>") if req else ""
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>Work Report</title>
<style>body{{font:14px/1.5 Segoe UI,Arial,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;color:#1b1b1b}}
h1{{font-size:22px;margin:0}}h2{{font-size:16px;border-bottom:2px solid #0b5cad;padding-bottom:4px;margin-top:28px}}
.kpi{{display:flex;gap:12px;flex-wrap:wrap}}.kpi div{{border:1px solid #d0d7de;border-radius:6px;padding:10px 14px;min-width:150px}}
.kpi b{{display:block;font-size:20px}}table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{border:1px solid #d0d7de;padding:5px 7px;text-align:left;vertical-align:top}}th{{background:#f3f6f9}}
.muted{{color:#57606a;font-size:12px}}@media print{{a{{color:inherit}}}}</style></head><body>
<h1>{title}</h1>
<p>{e(meta.get('Designation', ''))} · {e(meta.get('Level', ''))} · {e(meta.get('Team', ''))}<br>
<b>Period:</b> {e(a.frm)} to {e(a.to)}{' · <b>Project:</b> ' + e(a.project) if a.project else ''}</p>{req_html}
<h2>Summary</h2><div class="kpi">
<div><b>{total / 60:.1f} h</b>Logged time</div><div><b>{len(work)}</b>Activities</div>
<div><b>{(ev / len(work) * 100 if work else 0):.0f}%</b>With evidence link</div>
<div><b>{(high / len(work) * 100 if work else 0):.0f}%</b>High confidence</div></div>
<h2>Time by project</h2>{table(['Project', 'Hours', 'Share'], [[e(p), f'{m / 60:.1f}', f'{m / total * 100:.0f}%' if total else '-'] for p, m in sorted(byp.items(), key=lambda i: -i[1])])}
<h2>Time by activity</h2>{table(['Activity', 'Hours'], [[e(t), f'{m / 60:.1f}'] for t, m in sorted(byt.items(), key=lambda i: -i[1])])}
<h2>Timeline with evidence</h2>{table(['Date', 'Time', 'Min', 'Project', 'Ref', 'Type', 'Detail', 'Evidence', 'Conf.', 'ID'], timeline)}
<h2>Daily close-out and gaps</h2>{table(['Date', 'Total min', 'Summary'], [[e(x['date']), e(x['min']), e(x['detail'])] for x in closes]) if closes else '<p>No days closed in this period.</p>'}
<h2>Integrity</h2><p>Source: <code>{e(os.path.basename(LEDGER))}</code>, append-only, SHA-256 hash chain:
<b>{'intact' if chain_ok else 'BROKEN, rows were edited'}</b>. Confidence: high = system timestamp + artefact link; medium = artefact only; low = self-reported.<br>
<span class="muted">Generated {dt.datetime.now().isoformat(timespec='seconds')}. Report hash: REPORT_HASH</span></p></body></html>"""
    digest = hashlib.sha256(doc.encode()).hexdigest()
    doc = doc.replace("REPORT_HASH", digest)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"Wrote {a.out} | {len(work)} rows, {total / 60:.1f} h | sha256 {digest[:16]}")
    if req:
        r = append(dict(kind="share", date=dt.date.today().isoformat(), ref=req["id"], project=a.project,
                        detail=f"report {os.path.basename(a.out)} sha256 {digest[:16]}", src="eeh", conf="-"))
        print(f"{r['id']} logged share for {req['id']}")


def main():
    today = dt.date.today().isoformat()
    p = argparse.ArgumentParser(description="EEH work ledger")
    s = p.add_subparsers(dest="cmd", required=True)
    x = s.add_parser("init"); x.add_argument("--name", required=True); x.add_argument("--designation", required=True)
    x.add_argument("--level", default=""); x.add_argument("--team", default=""); x.add_argument("--hours", default="09:30-18:30")
    x = s.add_parser("add")
    for f in ("start", "end", "project", "ref", "type", "detail", "evidence", "conf"):
        x.add_argument(f"--{f}", default="")
    x.add_argument("--date", default=today); x.add_argument("--min", type=int); x.add_argument("--src", default="manual")
    x = s.add_parser("fix"); x.add_argument("--of", required=True); x.add_argument("--detail", required=True); x.add_argument("--evidence", default="")
    x = s.add_parser("close"); x.add_argument("--date", default=today)
    x = s.add_parser("show"); x.add_argument("--from", dest="frm", default=today); x.add_argument("--to", default=today)
    x.add_argument("--project"); x.add_argument("--kind")
    x = s.add_parser("req"); x.add_argument("--by", required=True); x.add_argument("--from", dest="frm", required=True)
    x.add_argument("--to", required=True); x.add_argument("--purpose", required=True); x.add_argument("--due", default="")
    x.add_argument("--project", default=""); x.add_argument("--evidence", default=""); x.add_argument("--src", default="manual")
    x = s.add_parser("report"); x.add_argument("--from", dest="frm", default=today); x.add_argument("--to", default=today)
    x.add_argument("--project"); x.add_argument("--req"); x.add_argument("--out", default="report.html")
    x = s.add_parser("timesheet"); x.add_argument("--from", dest="frm", required=True); x.add_argument("--to", required=True)
    x.add_argument("--project"); x.add_argument("--round", type=int, default=15); x.add_argument("--out", default="timesheet.csv")
    s.add_parser("verify")
    a = p.parse_args()
    globals()[f"cmd_{a.cmd}"](a)


if __name__ == "__main__":
    main()
