"""Build data/fixtures/usda_daily_export_sales.csv: USDA FAS daily export-sales announcements, 2016-2023 (D768).

The input is the raw collection cached at data/raw/usda/daily_sales/fas_daily_sales_raw_2016_2023.json.gz, gathered
in a browser on www.fas.usda.gov (the site answers non-browser clients with 403; nothing here spoofs a client):
  cards   every card of the FAS newsroom listing for the Export Sales Reporting Program (listing pages 23-102), kept
          when its listing year is 2016-2023, deduplicated by href: {d, href, title, tx}
  full    {href: the announcement page's <main article> text} for every card whose listing text could hide a sale
          (first sentence unfinished, a non-standard title, or nothing parsed from the listing text)
  js_csv  the same parse run in the browser by scripts/fas_daily_sales_parse.js, and its SHA-256

This module re-implements that parser in Python, line for line, and REFUSES to write the fixture unless its CSV is
byte-identical to the browser's: two implementations of one parse, in two languages, must agree on every row.

Run (system python):  python scripts/build_usda_daily_sales.py
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "usda" / "daily_sales" / "fas_daily_sales_raw_2016_2023.json.gz"
OUT = REPO / "data" / "fixtures" / "usda_daily_export_sales.csv"
META = REPO / "data" / "fixtures" / "usda_daily_export_sales.meta.json"

MONTHS = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6, "July": 7, "August": 8,
          "September": 9, "October": 10, "November": 11, "December": 12}
MON3 = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "June": 6, "Jul": 7, "July": 7, "Aug": 8,
        "Sep": 9, "Sept": 9, "Oct": 10, "Nov": 11, "Dec": 12, "March": 3, "April": 4}
CUT = re.compile(r"###|The U\.S\. Department of Agriculture is required|The marketing years? for|USDA issues both daily"
                 r"|Exporters are required|For further information|Related News")
NAME = r"[A-Z][A-Za-z'-]*(?: [A-Z][A-Za-z'-]*)*"
RE_SALE = re.compile(r"([\d,.]+)\s?(K)?\s?(?:metric tons|MT|tons)(?: of ([a-z][a-z ,]*?))?"
                     r"(?: for delivery| received during the reporting period for delivery)? to (?:the )?"
                     r"(unknown destinations?|" + NAME + r")")
RE_CHANGE = re.compile(r"([\d,.]+)\s?(K)?\s?(?:metric tons|MT|tons) of ([a-z][a-z ]*?) from (.+?) to (?:the )?(" + NAME + r")")
RE_HEAD = re.compile(r"(?:sales?|activity) (?:to|for) (?:the )?(unknown destinations?|" + NAME + r"):")
RE_HEADSALE = re.compile(r"([\d,.]+)\s?(K)?\s?(?:metric tons|MT|tons) of ([a-z][a-z ]*?)(?= -| –|,| for| during| received|\.|;| and)")
RE_MY = re.compile(r"(\d{4}/\d{2,4})")
COLS = ["date", "slug", "title_kind", "kind", "tonnes", "commodity", "destination", "my", "source", "status", "dateline",
        "dateline_date"]


class BuildError(RuntimeError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise BuildError(msg)


def iso_date(d: str) -> str:
    m = re.match(r"^(\w+) (\d{1,2}), (\d{4})$", d)
    return f"{m.group(3)}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}"


def dateline_of(text: str) -> str:
    m = re.search(r"WASHINGTON,? (\w+)\.? (\d{1,2}),? (\d{4})", text)
    if not m:
        return ""
    mo = MON3.get(m.group(1)) or MONTHS.get(m.group(1))
    return f"{m.group(3)}-{mo:02d}-{int(m.group(2)):02d}" if mo else ""


def norm_commodity(c: str | None) -> str:
    c = re.sub(r"\s+", " ", (c or "").lower()).strip()
    if re.search(r"soybean (cake and )?meal|soybean cake", c):
        return "soybean_meal"
    for pat, name in ((r"soybean oil", "soybean_oil"), (r"soybean", "soybeans"), (r"corn", "corn"), (r"wheat|durum", "wheat"),
                      (r"sorghum", "sorghum"), (r"barley", "barley"), (r"oats", "oats")):
        if re.search(pat, c):
            return name
    return "other:" + c if c else ""


def title_kind(t: str) -> str:
    if re.search(r"Statement|Notice of|Schedule Change|Keeps U\.S\.|Clarifies|Updates Schedule|Error in|Report Delayed", t, re.I):
        return "notice"
    if re.search(r"retraction", t, re.I):
        return "retraction"
    if re.search(r"correct", t, re.I):
        return "correction"
    if re.search(r"cancell?ation", t, re.I):
        return "cancellation"
    return "announcement"


def body_of(card: dict, full: dict) -> tuple[str, str]:
    f = full.get(card["href"])
    t = CUT.split(f or card["tx"], maxsplit=1)[0]
    w = t.find("WASHINGTON")
    m = re.search(r"Private exporters", t)
    i = w if w >= 0 else (m.start() if m else -1)
    if i >= 0:
        t = t[i:]
    return t, ("full" if f else "listing")


def restated_end(s: str) -> int:
    m = re.search(r"corrected announcement is as follows:", s, re.I)
    if not m:
        return 0
    k = m.start()
    after = s[k:]
    d = re.search(r"marketing year\.|\.\s", after)
    return k + (d.start() + 1 if d else len(after))


def js_round(v: float) -> int:
    return int(math.floor(v + 0.5))          # JavaScript Math.round for these positive values


def tonnes_of(num: str, k: str | None) -> int:
    v = float(num.replace(",", ""))
    return js_round(v * 1000) if k else js_round(v)


def parse_card(card: dict, full: dict) -> list[dict]:
    date = iso_date(card["d"])
    slug = re.sub(r"^/newsroom/", "", card["href"])
    tk = title_kind(card["title"])
    s, source = body_of(card, full)
    dl = dateline_of(s)
    base = {"date": date, "slug": slug, "title_kind": tk, "source": source,
            "dateline": "none" if not dl else ("match" if dl == date else "mismatch"), "dateline_date": dl}
    if tk == "notice":
        return [dict(base, kind="none", tonnes="", commodity="", destination="", my="", status="ok")]
    m0 = RE_MY.search(s)
    my_all = m0.group(1) if m0 else ""
    r_end = restated_end(s)

    def kind_of(idx: int, before: str) -> str:
        if tk in ("correction", "retraction") or idx < r_end:
            return "restated"
        if tk == "cancellation" or re.search(r"cancel", before, re.I):
            return "cancel"
        return "sale"

    def dest(d: str) -> str:
        return "unknown destinations" if d.startswith("unknown destination") else d.strip()

    rows: list[dict] = []
    if re.search(r"changes? in destination of", s, re.I) and r_end == 0:
        m = RE_CHANGE.search(s)
        rows.append(dict(base, kind="change", tonnes=tonnes_of(m.group(1), m.group(2)) if m else "",
                         commodity=norm_commodity(m.group(3)) if m else "", destination=m.group(5).strip() if m else "",
                         my=my_all, status="ok" if m else "unparsed"))
        return rows
    ml = re.search(r"reported (?:to [A-Za-z.' ]+? )?([a-z][a-z ]*?) sales of", s)
    last = ml.group(1).strip() if ml else ""
    for m in RE_SALE.finditer(s):
        com = re.sub(r",$", "", m.group(3)).strip() if m.group(3) else last
        if m.group(3):
            last = com
        before = s[max(0, m.start() - 80):m.start()]
        tail = s[m.start():m.start() + len(m.group(0)) + 70]
        mt = RE_MY.search(tail)
        rows.append(dict(base, kind=kind_of(m.start(), before), tonnes=tonnes_of(m.group(1), m.group(2)),
                         commodity=norm_commodity(com), destination=dest(m.group(4)), my=mt.group(1) if mt else my_all,
                         status="ok"))
    if not rows:
        h = RE_HEAD.search(s)
        if h:
            for m in RE_HEADSALE.finditer(s):
                before = s[max(0, m.start() - 80):m.start()]
                rows.append(dict(base, kind=kind_of(m.start(), before), tonnes=tonnes_of(m.group(1), m.group(2)),
                                 commodity=norm_commodity(m.group(3)), destination=dest(h.group(1)), my=my_all, status="ok"))
    if not rows:
        rows.append(dict(base, kind="none", tonnes="", commodity="", destination="", my=my_all, status="unparsed"))
    return rows


def to_csv(rows: list[dict]) -> str:
    def q(v) -> str:
        s = str(v)
        return '"' + s.replace('"', '""') + '"' if re.search(r'[",\n]', s) else s
    return "\n".join([",".join(COLS)] + [",".join(q(r[c]) for c in COLS) for r in rows]) + "\n"


def build() -> int:
    raw = json.loads(gzip.decompress(RAW.read_bytes()).decode("utf-8"))
    cards, full = raw["cards"], raw["full"]
    need(all(2016 <= int(c["d"][-4:]) <= 2023 for c in cards), "a card outside 2016-2023")
    need(len({c["href"] for c in cards}) == len(cards), "duplicate cards")
    rows = [r for c in cards for r in parse_card(c, full)]
    csv_text = to_csv(rows)
    js = raw["js_csv"]
    need(hashlib.sha256(js.encode("utf-8")).hexdigest() == raw["js_csv_sha256"], "the browser CSV does not match its own hash")
    if csv_text != js:
        a, b = csv_text.split("\n"), js.split("\n")
        diff = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y][:5]
        raise BuildError(f"Python parse != browser parse ({len(a)} vs {len(b)} lines); first differences: {diff}")
    need(not any(r["status"] == "unparsed" for r in rows), "an unparsed announcement")
    need(all(r["date"] < "2024-01-01" for r in rows), "a row dated 2024 or later")
    need(all(not r["my"] or r["my"][:4] <= "2024" for r in rows), "a marketing year starting after 2024 (a leaked related-news row?)")
    OUT.write_text(csv_text, encoding="utf-8", newline="\n")
    ev = lambda com: sorted({r["date"] for r in rows if r["kind"] == "sale" and r["commodity"] == com
                             and r["destination"] in ("China", "unknown destinations")})
    count = lambda key: {k: sum(1 for r in rows if r[key] == k) for k in sorted({r[key] for r in rows})}
    meta = {
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "builder": "scripts/build_usda_daily_sales.py",
        "reference_parser": "scripts/fas_daily_sales_parse.js (run in the browser; its CSV is byte-identical to this build's)",
        "source": raw["meta"], "raw_cache": str(RAW.relative_to(REPO)).replace("\\", "/"),
        "csv_sha256": hashlib.sha256(csv_text.encode("utf-8")).hexdigest(),
        "cards": len(cards), "full_pages": len(full), "rows": len(rows),
        "kind": count("kind"), "title_kind": count("title_kind"), "source_counts": count("source"), "dateline": count("dateline"),
        "dateline_mismatches": sorted({(r["date"], r["dateline_date"], r["slug"]) for r in rows if r["dateline"] == "mismatch"}),
        "event_days": {"soybeans_china_or_unknown": len(ev("soybeans")), "corn_china_or_unknown": len(ev("corn"))},
        "release_time": "09:00 ET on the business day after the exporter's report (FAS program page; in-text: 'issued at 9:00 a.m.', "
                        "FAS-ESR-088-20 and FAS-ESR-089-18)",
        "what_bites": [
            "date is the LISTING date. Where the 'WASHINGTON, <date>' dateline differs by 1-3 days (six 2016 announcements), the "
            "release day is ambiguous; D768 drops both days from the cell. Larger differences are typos (a wrong year or month).",
            "kind 'restated' rows re-state an EARLIER announcement inside a correction or retraction: never a new sale.",
            "a retraction withdraws a sale announced the same morning (2022-07-15, 133,000 t corn to China).",
            "'unknown destinations' is often China, but not always.",
            "full announcement pages carry a 'Related News' block listing the site's LATEST announcements; the parser cuts it "
            "before searching for the body, and the build refuses any marketing year beginning after 2024.",
        ],
    }
    META.write_text(json.dumps(meta, indent=1, default=list) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(rows)} rows from {len(cards)} cards ({len(full)} full pages); Python == browser parse; "
          f"event days: soybeans {meta['event_days']['soybeans_china_or_unknown']}, corn {meta['event_days']['corn_china_or_unknown']}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
