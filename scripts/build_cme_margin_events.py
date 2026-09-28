"""D657's margin events: parse CME's archived margin histories into one front-margin step series per root.

Reads the raw cache written by ``scripts/fetch_cme_margin_archive.py`` (the MAIN checkout's gitignored
``data/raw/cme_margins/history/``) and writes ``data/d657_margin_changes.csv`` (every change of each root's
front-month maintenance margin, with the file it came from), ``data/d657_margin_coverage.csv`` (which dates each
root's series covers, and its holes) and ``data/d657_margin_build.json`` (gate G0 and the counts).
No price is read here.

Three layouts, all CME's own, extracted with pypdf:
  H  "Performance Bond History for: A - B" (the ``{code}_2008_to_present.pdf`` files): a block per change date,
     one row per (Spec | Hedge/Member, contract tier) with Initial and Maintenance. The event list itself.
  D  daily tables (the ``2009_to_2013`` / ``2014_to_present`` zips and the ``2019-`` / ``2020-`` PDFs): one row per
     (business date, roll index), the front being roll index 1. Changes are read off the front's day-to-day values.
The quantity is the FRONT tier's maintenance margin. H also carries the speculator initial rate; the ratio of Spec
initial to maintenance is asserted (it is what makes a percentage change in maintenance the percentage change in
the initial margin D657 names).

    python scripts/build_cme_margin_events.py --selftest
    python scripts/build_cme_margin_events.py --build
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main_checkout() -> Path:
    for p in [REPO, *REPO.parents]:
        if p.name == "worktrees" and p.parent.name == ".claude":
            return p.parent.parent
    return REPO


RAW = main_checkout() / "data" / "raw" / "cme_margins"
OUT_CHANGES = REPO / "data" / "d657_margin_changes.csv"
OUT_COVERAGE = REPO / "data" / "d657_margin_coverage.csv"
OUT_BUILD = REPO / "data" / "d657_margin_build.json"

# CME clearing code -> breadth root (D657 section 1)
ROOT_OF = {"06": "ZM", "07": "ZL", "11": "YM", "17": "ZB", "21": "ZN", "25": "ZF", "26": "ZT", "48": "LE",
           "AD": "6A", "BP": "6B", "BTC": "BTC", "C": "ZC", "CD": "6C", "CL": "CL", "EC": "6E", "GC": "GC",
           "HG": "HG", "HO": "HO", "JY": "6J", "LN": "HE", "ND": "NQ", "NG": "NG", "NK": "NKD", "PL": "PL",
           "RB": "RB", "S": "ZS", "SF": "6S", "SI": "SI", "SP": "ES", "SR3": "SR3", "TN": "TN", "UBE": "UB",
           "W": "ZW"}
assert len(ROOT_OF) == 33 and len(set(ROOT_OF.values())) == 33

FNAME = re.compile(r"^([A-Za-z0-9]+)[-_](.+)__(\d{14})\.(pdf|zip)$")
H_SPAN = re.compile(r"Performance Bond History for:\s*(\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})")
H_BLOCK = re.compile(r"(\d{1,2}/\d{1,2}/\d{4})\s+ISO\s+Initial\s+Maintenance")
# two row orders: "1,650.00 1,500.00USDSpec ...Old Crop" and "Spec ...Mnth 1 USD 4,125.00 3,750.00"
H_ROW = re.compile(r"([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s*USD\s*(Spec|Hedge/Member)\s*\.\.\.\s*(.{0,60}?)"
                   r"(?=\s*[\d,]+\.\d{2}\s+[\d,]+\.\d{2}\s*USD|\s*\d{1,2}/\d{1,2}/\d{4}\s+ISO|\s*$)")
H_ROW2 = re.compile(r"(Spec|Hedge/Member)\s*\.\.\.\s*(.{0,60}?)\s*USD\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})")
H_FOOTER = re.compile(r"Page \d+ of \d+.*?cmegroup\.com|Performance Bond History for:\s*\S+\s*-\s*\S+|"
                      r"Minimum Performance Bond Requirements|Outright Rates")
D_ROW = re.compile(r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})(?:\s+\d{1,2}:\d{2})?\s+(.{1,80}?)\s+([A-Z]{3,6})\s+"
                   r"(\d+(?:\.\d+)?)\s+([A-Z0-9]+)-(\d{1,3})\b")


def pdate(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date() if "-" in s else datetime.strptime(s, "%m/%d/%Y").date()


def money(s: str) -> float:
    return float(s.replace(",", ""))


@dataclass(frozen=True)
class Step:
    """The front maintenance margin in force from ``d`` (as the file dates it)."""
    d: date
    maint: float
    init_spec: float | None


# ---------------------------------------------------------------- layout H


FRONT_LABEL = re.compile(r"^(?:m[a-z]*|tier)0?1(?!\d)")


def is_front(label: str) -> bool:
    """Tier labels seen: '' (one tier), 'Old Crop'/'New Crop', 'All Months', and month bands spelled 'Mnth 1',
    'Mnth1', 'Mth 1', 'Mths 1-4', 'Mnths 1-4', 'Mnth 1+', 'Tier 1'. The front is the tier that holds month 1."""
    n = re.sub(r"\s+", "", label.lower())
    return n == "" or n.startswith("oldcrop") or n == "allmonths" or bool(FRONT_LABEL.match(n))


def front_row(rows: list[tuple[float, float, str, str]]) -> tuple[float, float] | None:
    """(initial, maintenance) of the front tier's Spec row in one change block, or None.

    A block lists ONLY the tiers that changed that day (CL 2010-05-21 lists months 2-4, 5-10 and 11-18 and not
    month 1), so a block with no front-tier row is no change to the front, never a change to the first row."""
    for i, m, kind, lab in rows:
        if kind == "Spec" and is_front(lab.strip()):
            return i, m
    return None


def parse_h(text: str) -> tuple[list[Step], tuple[date, date], list[str]]:
    span = H_SPAN.search(text)
    if not span:
        raise ValueError("layout H without its 'Performance Bond History for' span")
    cover = (pdate(span.group(1)), pdate(span.group(2)))
    body = re.sub(r"\s+", " ", H_FOOTER.sub(" ", text))
    marks = list(H_BLOCK.finditer(body))
    steps, labels = [], []
    for k, mk in enumerate(marks):
        chunk = body[mk.end(): marks[k + 1].start() if k + 1 < len(marks) else len(body)]
        rows = [(money(a), money(b), kind, lab) for a, b, kind, lab in H_ROW.findall(chunk)]
        rows2 = [(money(a), money(b), kind, lab) for kind, lab, a, b in H_ROW2.findall(chunk)]
        if len(rows2) > len(rows):
            rows = rows2
        labels += sorted({lab.strip() for _, _, kind, lab in rows if kind == "Spec"})
        fr = front_row(rows)
        if fr is not None:
            steps.append(Step(pdate(mk.group(1)), fr[1], fr[0]))
    return steps, cover, labels


# ---------------------------------------------------------------- layout D


def parse_d(text: str, code: str) -> tuple[list[Step], tuple[date, date], int, str]:
    """The front (roll 1) series of the file's product. A daily table lists its rows under the clearing code
    or, for the index files (clearing code 11 is the $10 Dow), under the traded E-mini's symbol (YM); the
    clearing code is preferred, then the D657 root's symbol. Returns the product code used."""
    rows = D_ROW.findall(re.sub(r"\s+", " ", text))
    codes = {pc.upper() for *_, pc, roll in rows if int(roll) == 1}
    want = code.upper() if code.upper() in codes else ROOT_OF.get(code.upper(), "").upper()
    if want not in codes and len(codes) == 1:
        want = next(iter(codes))   # LC for live cattle (48), C1 / J1 in the 2014 FX zips: the file's only product
    by_day: dict[date, float] = {}
    n = 0
    for ds, _desc, _ex, m, pc, roll in rows:
        if pc.upper() != want or int(roll) != 1:
            continue
        n += 1
        d = pdate(ds)
        v = float(m)
        if d in by_day and by_day[d] != v:
            raise ValueError(f"{code}: two front margins on {d}: {by_day[d]} and {v}")
        by_day[d] = v
    if not by_day:
        raise ValueError(f"{code}: layout D with no front (roll 1) rows under {code} or its root; "
                         f"roll-1 codes present: {sorted(codes)[:10]}")
    days = sorted(by_day)
    steps = [Step(days[0], by_day[days[0]], None)]
    for d in days[1:]:
        if by_day[d] != steps[-1].maint:
            steps.append(Step(d, by_day[d], None))
    return steps, (days[0], days[-1]), n, want


# ---------------------------------------------------------------- files


def pdf_text(data: bytes) -> str:
    import pypdf
    r = pypdf.PdfReader(io.BytesIO(data))
    return "\n".join((p.extract_text() or "") for p in r.pages)


def parse_file(path: str) -> dict:
    p = Path(path)
    m = FNAME.match(p.name)
    code, era, capture, ext = m.group(1).upper(), m.group(2), m.group(3), m.group(4)
    data = p.read_bytes()
    if ext == "zip":
        z = zipfile.ZipFile(io.BytesIO(data))
        pdfs = [i for i in z.infolist() if i.filename.lower().endswith(".pdf")]
        if len(pdfs) != 1:
            raise ValueError(f"{p.name}: expected one PDF inside, found {[i.filename for i in z.infolist()]}")
        data = z.read(pdfs[0])
    out = {"file": p.name, "code": code, "era": era, "capture": capture}
    try:
        text = pdf_text(data)
        if H_SPAN.search(text):
            steps, cover, labels = parse_h(text)
            out.update(layout="H", tier_labels=sorted(set(labels)), rows=None, product=None)
        else:
            steps, cover, n, product = parse_d(text, code)
            out.update(layout="D", tier_labels=None, rows=n, product=product)
    except Exception as e:  # a file that does not parse is reported, never silently dropped
        out.update(layout="ERR", error=f"{type(e).__name__}: {e}", cover=None, steps=[])
        return out
    out["cover"] = [cover[0].isoformat(), cover[1].isoformat()]
    out["steps"] = [[s.d.isoformat(), s.maint, s.init_spec] for s in steps]
    return out


def inventory() -> list[Path]:
    files = sorted((RAW / "history").glob("*__*.*"))
    keep = [f for f in files if FNAME.match(f.name) and FNAME.match(f.name).group(1).upper() in ROOT_OF]
    return keep


# ---------------------------------------------------------------- selftest


def selftest() -> None:
    h = ("Minimum Performance Bond Requirements Performance Bond History for: 01/24/2008 - 02/24/2015 "
         "Outright Rates 3/11/2008 ISO Initial Maintenance 1,650.00 1,500.00USDSpec ...Old Crop "
         "1,500.00 1,500.00USDHedge/Member ...Old Crop 1,650.00 1,500.00USDSpec ...New Crop "
         "3/18/2008 ISO Initial Maintenance 2,200.00 2,000.00USDSpec ...Old Crop "
         "2,000.00 2,000.00USDHedge/Member ...Old Crop Page 1 of 32/24/2015 20 South Wacker Drive Chicago, IL "
         "60606 Ph.: (312) 930-317 Fax: (312) 930-3187 cmegroup.com Performance Bond History for: 01/24/2008 - "
         "02/24/2015 6/3/2008 ISO Initial Maintenance 1,980.00 1,800.00USDSpec ... 1,800.00 1,800.00USDHedge/Member ...")
    steps, cover, labels = parse_h(h)
    assert cover == (date(2008, 1, 24), date(2015, 2, 24)), cover
    assert [(s.d, s.maint, s.init_spec) for s in steps] == [
        (date(2008, 3, 11), 1500.0, 1650.0), (date(2008, 3, 18), 2000.0, 2200.0), (date(2008, 6, 3), 1800.0, 1980.0)], steps
    # the front is the nearby tier, not the first row, when a band list leads with a later month
    assert front_row([(9.0, 8.0, "Spec", "Mnth 2-4"), (5.5, 5.0, "Spec", "Mnth 1"), (5.0, 5.0, "Hedge/Member", "")]) == (5.5, 5.0)
    # a block that does not list the front tier is no front change (CL 2010-05-21)
    assert front_row([(4125.0, 3750.0, "Spec", "Mnth 2-4"), (4125.0, 3750.0, "Spec", "Mnth 5-10")]) is None
    for lab, want in [("Mnth1", True), ("Mth 1", True), ("Mths 1-4", True), ("Mnths 1-4", True), ("Tier 1", True),
                      ("Mnth 1+", True), ("All Months", True), ("Old Crop", True), ("", True), ("Mnth10", False),
                      ("Mnth 11-18", False), ("New Crop", False), ("Tier 2", False), ("Summer 2014", False)]:
        assert is_front(lab) is want, (lab, want)
    # the label-first row order, and an unlabeled Spec row followed directly by its Hedge row
    s2, _, _ = parse_h("Performance Bond History for: 01/01/2008 - 02/24/2015 4/23/2010 ISO Initial Maintenance "
                       "Spec ...Mnth 1 USD 4,125.00 3,750.00 Hedge/Member ...Mnth 1 USD 3,750.00 3,750.00 "
                       "Spec ...Mnth 2-4 USD 3,575.00 3,250.00 5/21/2010 ISO Initial Maintenance "
                       "Spec ...Mnth 2-4 USD 4,125.00 3,750.00")
    assert [(s.d, s.maint) for s in s2] == [(date(2010, 4, 23), 3750.0)], s2
    s3, _, lab3 = parse_h("Performance Bond History for: 01/01/2009 - 08/15/2016 1/5/2011 ISO Initial Maintenance "
                          "4,400.00 4,000.00USDSpec ... 4,000.00 4,000.00USDHedge/Member ... "
                          "4,950.00 4,500.00USDSpec ...Mths 5-6 4,500.00 4,500.00USDHedge/Member ...Mths 5-6")
    assert [(s.d, s.maint) for s in s3] == [(date(2011, 1, 5), 4000.0)] and lab3 == ["", "Mths 5-6"], (s3, lab3)
    d = ("Business Date Description Exchange Margin Roll Product Code "
         "12/31/2013 0:00 SOYBEAN MEAL FUTURES CBT 2250 06-1 12/31/2013 0:00 SOYBEAN MEAL FUTURES CBT 2000 06-7 "
         "12/30/2013 0:00 SOYBEAN MEAL FUTURES CBT 2250 06-1 12/27/2013 0:00 SOYBEAN MEAL FUTURES CBT 2000 06-1 "
         "2014-01-02 SOYBEAN MEAL FUTURES CBT 2250 06-01 2014-01-02 SOYBEAN MEAL MINI CBT 400 YM-1")
    steps, cover, n, pc = parse_d(d, "06")
    assert pc == "06" and n == 4 and cover == (date(2013, 12, 27), date(2014, 1, 2)), (pc, n, cover)
    # clearing code 11 (the $10 Dow) lists the traded E-mini under YM: the root's symbol is taken
    s11, _, n11, pc11 = parse_d("2014-01-02 E-MINI DOW ($5) FUTURES CBT 4000 YM-1 "
                                "2014-01-03 E-MINI DOW ($5) FUTURES CBT 4400 YM-1", "11")
    assert pc11 == "YM" and n11 == 2 and [s.maint for s in s11] == [4000.0, 4400.0], (pc11, s11)
    assert [(s.d, s.maint) for s in steps] == [(date(2013, 12, 27), 2000.0), (date(2013, 12, 30), 2250.0)], steps
    # cleaning: a holiday zero and a one-day spike vanish; a genuine large step that is not reversed stays
    st, rem = clean_steps([["2010-09-01", 2500.0, None], ["2010-09-23", 12500.0, None], ["2010-09-24", 2500.0, None],
                           ["2014-05-26", 0.0, None], ["2014-05-27", 2500.0, None], ["2014-06-02", 4000.0, None]])
    assert st == [["2010-09-01", 2500.0, None], ["2014-06-02", 4000.0, None]], st
    assert len(rem) == 2 and rem[0]["why"].startswith("non-positive") and rem[1]["why"].startswith("transient"), rem
    # an event-sized step undone the next day goes; one held for a week stays
    st, rem = clean_steps([["2010-01-01", 1000.0, None], ["2010-01-04", 1100.0, None], ["2010-01-05", 1000.0, None],
                           ["2010-02-01", 1100.0, None], ["2010-02-08", 1000.0, None]])
    assert [s[1] for s in st] == [1000.0, 1100.0, 1000.0] and len(rem) == 1, (st, rem)
    try:
        parse_d("2014-01-02 X FUT CBT 100 06-01 2014-01-02 X FUT CBT 200 06-01", "06")
    except ValueError:
        pass
    else:
        raise AssertionError("two front margins on one day must raise")
    print("selftest OK")


# ---------------------------------------------------------------- stitching and gates

# Under SPAN 2 the margin is a VaR model's output, not a set table; a "change" there is not the same event.
# Excluded by rule, fixed before any series was looked at (D657 build, 2026-09-28).
SPAN2_FROM = {"CL": date(2023, 10, 20), "NG": date(2023, 10, 20), "RB": date(2023, 10, 20),
              "HO": date(2023, 10, 20), "SP": date(2024, 10, 18), "11": date(2024, 10, 18),
              "ND": date(2024, 10, 18), "NK": date(2024, 10, 18)}
MIN_PCT = 0.05          # D657 section 1: an increase of at least 5 %
HOLE_DAYS = 7           # a gap of more than a week between covered spans is a hole
IN_SAMPLE_END = date(2023, 12, 15)


def iso(s: str) -> date:
    return date.fromisoformat(s)


def clean_steps(steps: list[list]) -> tuple[list[list], list[dict]]:
    """Remove what is not a margin: holiday placeholder rows carrying 0 (YM and NQ on 2014-05-26, Memorial Day),
    and one-off steps, a step of >= MIN_PCT either way reversed to within 1 % inside three days (wheat, 2010-09-23:
    2,500 -> 12,500 -> 2,500; corn, 2010-01-04: 1,000 -> 1,100 -> 1,000). Consecutive equal levels are then merged.
    Everything removed is returned."""
    removed = [{"date": d, "maint": m, "why": "non-positive (holiday placeholder)"} for d, m, _ in steps if m <= 0]
    st = [s for s in steps if s[1] > 0]
    changed = True
    while changed:
        changed = False
        for k in range(1, len(st) - 1):
            (d0, m0, _), (d1, m1, _), (d2, m2, _) = st[k - 1], st[k], st[k + 1]
            # any step that would count as an event (>= MIN_PCT) and is undone within three days: CME does not
            # raise a margin and cut it back the next session (ZC 2010-01-04 +10 %, 2010-01-05 -9 %)
            big = m1 / m0 - 1 >= MIN_PCT or m0 / m1 - 1 >= MIN_PCT
            if big and (iso(d2) - iso(d1)).days <= 3 and abs(m2 / m0 - 1) <= 0.01:
                removed.append({"date": d1, "maint": m1, "why": f"transient: {m0} -> {m1} -> {m2} by {d2}"})
                st = st[:k] + st[k + 2:] if abs(m2 - m0) < 1e-9 else st[:k] + st[k + 1:]
                changed = True
                break
    out = []
    for s in st:
        if not out or s[1] != out[-1][1]:
            out.append(s)
    return out, removed


def pct_agree(a: dict, b: dict) -> float | None:
    r = agreement(a, b)
    return r["pct_same_day"] / r["n"] if r and r["n"] else None


def mislabeled(by_code: dict[str, list[dict]]) -> list[dict]:
    """A change-log file identical to another product's change-log file, where the two disagree about which
    product's daily table they match, is the other product's file (the archived corn 2008_to_present.pdf is
    soybeans' history, line for line). The copy that agrees with its OWN product's daily tables is kept."""
    hs = [q for qs in by_code.values() for q in qs if q["layout"] == "H" and q["steps"]]
    out = []
    for i, a in enumerate(hs):
        for b in hs[i + 1:]:
            if a["code"] == b["code"]:
                continue
            sa, sb = {(d, m) for d, m, _ in a["steps"]}, {(d, m) for d, m, _ in b["steps"]}
            if len(sa & sb) < 0.9 * min(len(sa), len(sb)):
                continue
            own = {}
            for q in (a, b):
                ds = [d for d in by_code[q["code"]] if d["layout"] == "D" and usable(d)]
                vals = [v for v in (pct_agree(q, d) for d in ds) if v is not None]
                own[q["file"]] = max(vals) if vals else None
            ranked = sorted((a, b), key=lambda q: -1 if own[q["file"]] is None else own[q["file"]])
            loser = ranked[0]
            out.append({"excluded": loser["file"], "duplicate_of": ranked[1]["file"],
                        "own_daily_agreement": own, "shared_steps": len(sa & sb)})
    return out


def usable(q: dict) -> bool:
    """A file is used unless it lies wholly inside its product's SPAN 2 era."""
    cut = SPAN2_FROM.get(q["code"])
    return cut is None or iso(q["cover"][0]) < cut


def clip(q: dict) -> tuple[date, date]:
    lo, hi = iso(q["cover"][0]), iso(q["cover"][1])
    cut = SPAN2_FROM.get(q["code"])
    if cut is not None and hi >= cut:
        hi = cut - timedelta(days=1)
    return lo, hi


def increases(q: dict, lo: date, hi: date) -> list[tuple[date, float, float]]:
    """(date, old, new) for every front increase of >= MIN_PCT inside [lo, hi], from one file's own steps."""
    st = [(iso(d), m) for d, m, _ in q["steps"]]
    out = []
    for (d0, m0), (d1, m1) in zip(st, st[1:]):
        if lo <= d1 <= hi and m0 > 0 and m1 / m0 - 1 >= MIN_PCT:
            out.append((d1, m0, m1))
    return out


def agreement(a: dict, b: dict) -> dict:
    """G0-c for one pair of files of one product: the share of a's increases in the overlap that b carries on
    the same date with the same new amount (and, reported beside it, within 1 and 3 calendar days)."""
    lo = max(clip(a)[0], clip(b)[0])
    hi = min(clip(a)[1], clip(b)[1])
    if lo > hi:
        return {}
    ia = increases(a, lo, hi)
    bs = [(iso(d), m) for d, m, _ in b["steps"]]

    def level(d: date):  # b's level in force on d
        v = None
        for dd, m in bs:
            if dd <= d:
                v = m
            else:
                break
        return v

    def found(d: date, new: float, tol: int) -> bool:
        return any(level(d + timedelta(days=k)) == new and level(d + timedelta(days=k - 1)) != new
                   for k in range(-tol, tol + 1))

    def found_pct(d: date, old: float, new: float, tol: int) -> bool:
        """b has a step of the same percentage (within half a point) on d, within tol days: the check that
        survives two files quoting different contract sizes of one product (the $10 Dow and the E-mini)."""
        for k in range(-tol, tol + 1):
            v1, v0 = level(d + timedelta(days=k)), level(d + timedelta(days=k - 1))
            if v1 and v0 and v1 != v0 and abs((v1 / v0) - (new / old)) <= 0.005:
                return True
        return False

    exact = sum(found(d, new, 0) for d, _, new in ia)
    near1 = sum(found(d, new, 1) for d, _, new in ia)
    near3 = sum(found(d, new, 3) for d, _, new in ia)
    pct0 = sum(found_pct(d, old, new, 0) for d, old, new in ia)
    pct1 = sum(found_pct(d, old, new, 1) for d, old, new in ia)
    return {"a": a["file"], "b": b["file"], "overlap": [lo.isoformat(), hi.isoformat()], "n": len(ia),
            "exact": exact, "within_1d": near1, "within_3d": near3, "pct_same_day": pct0, "pct_within_1d": pct1,
            "products": [a.get("product") or "H", b.get("product") or "H"]}


def stitch(qs: list[dict]) -> tuple[list[dict], list[list[str]]]:
    """One product's front series: layout-H files first (CME's change log), daily tables where no H file
    covers. Returns the changes (both directions, each from inside ONE file's covered span, so a step across a
    hole is never a change) and the covered spans."""
    qs = [q for q in qs if usable(q)]
    order = sorted(qs, key=lambda q: (q["layout"] != "H", -int(q["capture"])))
    spans: list[tuple[date, date, dict]] = []
    for q in order:
        lo, hi = clip(q)
        # the parts of [lo, hi] no earlier-priority file covers
        pieces = [(lo, hi)]
        for a, b, _ in spans:
            nxt = []
            for x, y in pieces:
                if y < a or x > b:
                    nxt.append((x, y))
                    continue
                if x < a:
                    nxt.append((x, a - timedelta(days=1)))
                if y > b:
                    nxt.append((b + timedelta(days=1), y))
            pieces = nxt
        spans += [(x, y, q) for x, y in pieces if x <= y]
    spans.sort(key=lambda s: s[0])
    changes = []
    for lo, hi, q in spans:
        st = [(iso(d), m) for d, m, _ in q["steps"]]
        for (d0, m0), (d1, m1) in zip(st, st[1:]):
            if lo < d1 <= hi and m0 > 0:
                changes.append({"date": d1.isoformat(), "old": m0, "new": m1, "pct": m1 / m0 - 1,
                                "file": q["file"], "layout": q["layout"]})
    # merge touching spans into covered ranges for the coverage table
    cov: list[list[date]] = []
    for lo, hi, _ in spans:
        if cov and (lo - cov[-1][1]).days <= HOLE_DAYS:
            cov[-1][1] = max(cov[-1][1], hi)
        else:
            cov.append([lo, hi])
    return changes, [[a.isoformat(), b.isoformat()] for a, b in cov]


def parsed_all(files: list[Path], workers: int) -> list[dict]:
    """Parse every file, cached in temp/ on (file name, size) and this module's mtime."""
    cache_p = REPO / "temp" / "d657_parsed_cache.json"
    stamp = Path(__file__).stat().st_mtime_ns
    cache = {}
    if cache_p.exists():
        c = json.load(open(cache_p, encoding="utf-8"))
        if c.get("stamp") == stamp:
            cache = c["files"]
    todo = [f for f in files if cache.get(f.name, {}).get("size") != f.stat().st_size]
    if todo:
        print(f"parsing {len(todo)} files ({len(files) - len(todo)} cached) on {workers} processes", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for f, q in zip(todo, ex.map(parse_file, [str(f) for f in todo])):
                cache[f.name] = {"size": f.stat().st_size, "q": q}
        (REPO / "temp").mkdir(exist_ok=True)
        json.dump({"stamp": stamp, "files": cache}, open(cache_p, "w", encoding="utf-8"))
    return [cache[f.name]["q"] for f in files]


def build(workers: int) -> None:
    files = inventory()
    if not files:
        raise SystemExit(f"no history files under {RAW / 'history'}")
    allq = parsed_all(files, workers)
    errors = [{"file": q["file"], "error": q["error"]} for q in allq if q["layout"] == "ERR"]
    parsed = [q for q in allq if q["layout"] != "ERR"]
    for q in parsed:
        print(f"{q['code']:>4} {q['layout']} {q['era']:<28} cover {q['cover'][0]} -> {q['cover'][1]} "
              f"steps {len(q['steps']):>4}" + (f" product {q['product']}" if q.get("product") else "")
              + (f" tiers {q['tier_labels']}" if q["tier_labels"] else ""))
    for e in errors:
        print("  NOT PARSED:", e["file"], "|", e["error"][:160])

    # G0-a's amount check runs on the raw parse; placeholders and spikes are then removed and listed
    bad_amounts = [q["file"] for q in parsed if any(m <= 0 for _, m, _ in q["steps"])]
    cleaned = []
    for q in parsed:
        q["steps"], rem = clean_steps(q["steps"])
        cleaned += [{"file": q["file"], **r} for r in rem]

    by_code: dict[str, list[dict]] = {}
    for q in parsed:
        by_code.setdefault(q["code"], []).append(q)
    wrong = mislabeled(by_code)
    drop = {w["excluded"] for w in wrong}
    for w in wrong:
        print("  MISLABELED, excluded:", w)
    for code in by_code:
        by_code[code] = [q for q in by_code[code] if q["file"] not in drop]
    parsed = [q for q in parsed if q["file"] not in drop]

    missing = sorted(set(ROOT_OF) - set(by_code))

    # the Spec-initial / maintenance ratio, wherever layout H carries both
    ratios = sorted({round(i / m, 4) for q in parsed if q["layout"] == "H" for _, m, i in q["steps"] if i and m})

    # G0-c: agreement between overlapping files of one product
    pairs = []
    for code, qs in by_code.items():
        us = sorted([q for q in qs if usable(q)], key=lambda q: q["cover"][0])
        for i in range(len(us)):
            for j in range(len(us)):
                if i != j:
                    r = agreement(us[i], us[j])
                    if r and r["n"]:
                        pairs.append(r)
    n_all = sum(r["n"] for r in pairs)
    pooled = {k: (sum(r[k] for r in pairs) / n_all if n_all else None)
              for k in ("exact", "within_1d", "within_3d", "pct_same_day", "pct_within_1d")}
    # A change log for the index codes quotes the big contract ($10 Dow, big Nasdaq) while the daily tables
    # quote the traded E-mini, so their AMOUNTS cannot agree by construction. The design's bar (same date, same
    # new amount) is applied to pairs quoting one contract; the cross-size pairs are held to the same date and
    # the same percentage. Both are reported.
    cross = [r for r in pairs if "H" in r["products"] and any(p in ("YM", "NQ", "ES", "NKD") for p in r["products"])]
    same = [r for r in pairs if r not in cross]
    n_same, n_cross = sum(r["n"] for r in same), sum(r["n"] for r in cross)
    same_exact = sum(r["exact"] for r in same) / n_same if n_same else None
    cross_pct = sum(r["pct_same_day"] for r in cross) / n_cross if n_cross else None

    rows, cov_rows = [], []
    for code in sorted(by_code):
        changes, cov = stitch(by_code[code])
        for c in changes:
            rows.append({"root": ROOT_OF[code], "code": code, **c})
        for lo, hi in cov:
            cov_rows.append({"root": ROOT_OF[code], "code": code, "from": lo, "to": hi})

    import csv
    with open(OUT_CHANGES, "w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, ["root", "code", "date", "old", "new", "pct", "file", "layout"], lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r["root"], r["date"])):
            w.writerow({**r, "pct": f"{r['pct']:.6f}"})
    with open(OUT_COVERAGE, "w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, ["root", "code", "from", "to"], lineterminator="\n")
        w.writeheader()
        w.writerows(cov_rows)

    inc = [r for r in rows if r["pct"] >= MIN_PCT and iso(r["date"]) <= IN_SAMPLE_END]
    per_root = {}
    for r in inc:
        per_root[r["root"]] = per_root.get(r["root"], 0) + 1
    per_year = {}
    for r in inc:
        y = r["date"][:4]
        per_year[y] = per_year.get(y, 0) + 1
    out = {
        "decision_record": "docs/decisions/D657-STAGE-0-DESIGN-margin-hikes-forced-exit-and-reversion.md",
        "reads_no_price": True,
        "files": len(allq), "files_parsed": len(parsed), "files_not_parsed": errors, "codes": len(by_code),
        "G0a": {"missing_codes": missing, "files_with_nonpositive_rows": bad_amounts,
                "nonpositive_rows_are_holiday_placeholders_removed": True,
                "pass": not missing},
        "removed_steps": cleaned,
        "mislabeled_files_excluded": wrong,
        "spec_initial_over_maintenance": ratios,
        "G0c": {"pairs": pairs, "increases_compared": n_all, "pooled": pooled,
                "same_contract": {"increases": n_same, "exact": same_exact},
                "cross_size": {"increases": n_cross, "pct_same_day": cross_pct,
                               "why": "the index change logs quote the big contract, the daily tables the E-mini"},
                "pass": bool(n_same) and same_exact >= 0.95 and (not n_cross or cross_pct >= 0.95)},
        "span2_excluded_from": {ROOT_OF[k]: v.isoformat() for k, v in SPAN2_FROM.items()},
        "in_sample_increases_unmerged": len(inc), "per_root": dict(sorted(per_root.items())),
        "per_year": dict(sorted(per_year.items())),
        "note": "increases are >= 5 % front maintenance steps before merging; the runner merges within 10 sessions",
    }
    json.dump(out, open(OUT_BUILD, "w", encoding="utf-8", newline="\n"), indent=1)
    print(json.dumps({k: out[k] for k in ("G0a", "spec_initial_over_maintenance", "in_sample_increases_unmerged",
                                          "per_year")}, indent=1))
    print("G0-c pooled", pooled, "over", n_all, "increases in", len(pairs), "file pairs")
    for r in pairs:
        if r["exact"] < r["n"]:
            print("  disagreement:", r)
    print("coverage per root:")
    for code in sorted(by_code):
        print(f"  {ROOT_OF[code]:>4}", "  ".join(f"{c['from']}->{c['to']}" for c in cov_rows if c["code"] == code))


OUT_NOTICES = REPO / "data" / "d657_margin_notices.csv"
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
ADV_DATE = re.compile(rf"\bDATE:\s*(?:\w+day,\s*)?((?:{MONTHS})\s+\d{{1,2}},\s*\d{{4}})", re.I)
ADV_EFF = re.compile(rf"effective\s+(?:after\s+the\s+close\s+of\s+business\s+)?(?:on\s+)?(?:\w+day,\s*)?"
                     rf"((?:{MONTHS})\s+\d{{1,2}},\s*\d{{4}})", re.I)


def notices() -> None:
    """Notice and effective dates of the archived performance-bond advisories (D657 A1: notice dates only).
    An advisory is a performance-bond one when its subject says so; its notice date is its DATE line and its
    effective date the first 'effective ... <date>' in its text."""
    import csv
    files = sorted((RAW / "advisories").glob("Chadv*.pdf"))
    rows, skipped = [], 0
    for f in files:
        try:
            import pypdf
            r = pypdf.PdfReader(str(f))
            t = re.sub(r"\s+", " ", " ".join((p.extract_text() or "") for p in r.pages[:2]))
        except Exception:
            skipped += 1
            continue
        subj = re.search(r"SUBJECT:\s*(.{0,120})", t, re.I)
        if not subj or "performance bond" not in subj.group(1).lower():
            continue
        dm, em = ADV_DATE.search(t), ADV_EFF.search(t)
        if not dm or not em:
            skipped += 1
            continue
        nd = datetime.strptime(re.sub(r"\s+", " ", dm.group(1).replace(" ,", ",")), "%B %d, %Y").date()
        ed = datetime.strptime(re.sub(r"\s+", " ", em.group(1).replace(" ,", ",")), "%B %d, %Y").date()
        if not (0 <= (ed - nd).days <= 14):
            skipped += 1
            continue
        rows.append({"advisory": f.name.split("__")[0], "notice": nd.isoformat(), "effective": ed.isoformat()})
    with open(OUT_NOTICES, "w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, ["advisory", "notice", "effective"], lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r["effective"]))
    gaps = pd_gaps([(date.fromisoformat(r["effective"]) - date.fromisoformat(r["notice"])).days for r in rows])
    print(f"advisories read {len(files)}, performance-bond with both dates {len(rows)}, skipped {skipped}; "
          f"effective - notice (calendar days): {gaps}")


def pd_gaps(xs: list[int]) -> dict:
    out: dict[int, int] = {}
    for x in xs:
        out[x] = out.get(x, 0) + 1
    return dict(sorted(out.items()))


def handcheck(roots: list[str], per_root: int = 10, seed: int = 657) -> None:
    """G0-b: draw changes by seed and print each beside the source text it was parsed from, for a reader to
    check. The text is pypdf's extraction of the page, not a rendering of it (no renderer on this machine)."""
    import csv
    import random
    rows = list(csv.DictReader(open(OUT_CHANGES, encoding="utf-8")))
    rng = random.Random(seed)
    texts: dict[str, str] = {}
    for root in roots:
        pool = [r for r in rows if r["root"] == root] if root != "pre2014" else \
            [r for r in rows if r["date"] < "2014-01-01" and r["layout"] == "H"]
        pick = sorted(rng.sample(pool, min(per_root, len(pool))), key=lambda r: r["date"])
        print(f"\n######## {root}: {len(pick)} of {len(pool)} changes")
        for r in pick:
            f = RAW / "history" / r["file"]
            if r["file"] not in texts:
                data = f.read_bytes()
                if f.suffix == ".zip":
                    z = zipfile.ZipFile(io.BytesIO(data))
                    data = z.read([i for i in z.infolist() if i.filename.lower().endswith(".pdf")][0])
                texts[r["file"]] = re.sub(r"\s+", " ", pdf_text(data))
            t = texts[r["file"]]
            d = date.fromisoformat(r["date"])
            keys = [d.isoformat(), f"{d.month}/{d.day}/{d.year}"]
            hits = [m.start() for k in keys for m in [re.search(r"(?<![\d/])" + re.escape(k) + r"(?!\d)", t)] if m]
            hit = hits[0] if hits else -1
            ctx = t[max(0, hit - 20): hit + 260] if hit >= 0 else "(date not found in text)"
            print(f"- {r['root']} {r['date']} {float(r['old']):,.0f} -> {float(r['new']):,.0f} ({float(r['pct']):+.1%}) "
                  f"[{r['layout']}] {r['file']}\n    text: {ctx}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--handcheck", nargs="*", metavar="ROOT")
    ap.add_argument("--notices", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.selftest:
        selftest()
    if a.build:
        build(a.workers)
    if a.handcheck is not None:
        handcheck(a.handcheck or ["GC", "CL", "ZC", "pre2014"])
    if a.notices:
        notices()
    if not (a.selftest or a.build or a.handcheck is not None or a.notices):
        ap.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
