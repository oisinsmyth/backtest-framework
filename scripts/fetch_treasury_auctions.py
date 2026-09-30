"""D710 FIXTURE (NETWORK): the Treasury coupon auction calendar, with the competitive close time and the takedown.

    python scripts/fetch_treasury_auctions.py --probe     # one request: the field list and the total count
    python scripts/fetch_treasury_auctions.py --fetch     # Fiscal Data (all Note/Bond auctions from 2009) + the G8
                                                          # TreasuryDirect sample -> data/raw/treasury_auctions/
    python scripts/fetch_treasury_auctions.py --build     # raw -> data/calendar/treasury_auctions.csv + .meta.json
    python scripts/fetch_treasury_auctions.py --selftest  # every gate passes a clean case and RAISES on a break

D585's pattern (`fetch_release_calendar.py`): stdlib only; the raw responses are kept byte for byte under a
fetched-at name with a `_manifest.json` (url, accessed_utc, bytes, sha256); the build refuses a row it cannot source.

SOURCE
------
Fiscal Data, "Treasury Securities Auctions Data", keyless:
  https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query
  filter=security_type:in:(Note,Bond),auction_date:gte:2009-01-01, page[size]=10000, paginated.
The schema was probed for D710 on 2026-09-30 (114 fields). The fields used are named in COLS_FD below.
There is NO results-release-time field; D710 section 5 fixes the post window at 13:05 on the paper's p. 14.

The calendar is a SCHEDULE, not a price. It is fetched in full; D710's runner cuts it below 2024-01-01 at read.

WHAT A ROW IS
-------------
One Note or Bond auction (bills and CMBs are not in the query). `kind` is NOMINAL, TIPS (inflation_index_security
= Yes) or FRN (floating_rate = Yes). `tenor` is the term the auction was SOLD as: the ORIGINAL term for a routine
reopening (whose security_term is the remaining one), but `security_term` where Treasury met a standard auction by
reopening an older issue and security_term is itself a whole standard term (`tenor_rule` = as_auctioned; see
`classify`). `small_value_test` flags Treasury's $25m contingency auctions (offering < $1bn): not supply events,
not counted by G2, not in any shared day.
`close_comp_et` is `closing_time_comp` parsed; a row whose close is missing or unparsable is NOT written -- it goes
to the meta's `not_sourced` and is never assumed to be 13:00. `pd_share` = primary_dealer_accepted / comp_accepted.
`shared_day` names the other fixed-rate or FRN coupon auctions on the same date (G5).

GATES (each proven to raise by --selftest, at the gate named)
-------------------------------------------------------------
  G1 every row has source_url, accessed_utc and method 'fetched'
  G2 per calendar year 2010..2025, each nominal tenor 2/3/5/7/10/30y has 12 auctions; 20y 0 before 2020-05 and 12 a
     year from 2021 (8 in 2020); any other count must be NAMED in SHORT_YEARS with a reason
  G3 every written row's close parses; closes other than 13:00, 11:30, 11:00 are listed
  G4 no duplicate (cusip, auction_date)
  G5 shared days listed by type (nominal-nominal, nominal-tips, nominal-frn, tips-frn)
  G6 an original_security_term outside the known set RAISES
  G7 0 <= pd_share <= 1 and comp_accepted > 0 on every row with results
  G8 24 nominal auctions (seed 710, 2010..2023) re-read from TreasuryDirect's own securities API: auction date and
     close time must AGREE (they are the event clock -- a disagreement raises); offering amount and primary-dealer
     accepted are compared and every disagreement is LISTED, never overwritten; at least 22 of 24 must be checkable
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from d710_paths import REPO, data_root, tracked  # noqa: E402

API = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query"
FILTER = "security_type:in:(Note,Bond),auction_date:gte:2009-01-01"
PAGE = 10000
TD_SEARCH = "https://www.treasurydirect.gov/TA_WS/securities/search?cusip={cusip}&format=json"
UA = {"User-Agent": "backtest-framework-fetch/1.0 (personal research; contact via repository)",
      "Accept": "application/json"}
PAUSE = 1.0
ET = ZoneInfo("America/New_York")
OUT_CSV = tracked("calendar", "treasury_auctions.csv")
OUT_META = tracked("calendar", "treasury_auctions.meta.json")

TENORS = {"2-Year": "2y", "3-Year": "3y", "5-Year": "5y", "7-Year": "7y", "10-Year": "10y", "20-Year": "20y",
          "30-Year": "30y"}
NOMINAL_TENORS = ("2y", "3y", "5y", "7y", "10y", "20y", "30y")
G2_YEARS = range(2010, 2026)
USUAL_CLOSES = ("13:00", "11:30", "11:00")
G8_N, G8_MIN, G8_SEED = 24, 22, 710
# a year outside G2's rule must be named here with a reason BEFORE the build reads it; filled from the sources
SHORT_YEARS: dict[tuple[str, int], str] = {
    ("20y", 2020): "the 20-year bond was reintroduced with its first auction in May 2020 (8 auctions May-Dec)",
}
COLS_FD = ("record_date", "cusip", "security_type", "security_term", "original_security_term", "auction_date",
           "issue_date", "maturity_date", "reopening", "inflation_index_security", "floating_rate",
           "cash_management_bill_cmb", "closing_time_comp", "closing_time_noncomp", "offering_amt", "comp_accepted",
           "primary_dealer_accepted", "direct_bidder_accepted", "indirect_bidder_accepted", "total_accepted",
           "soma_accepted", "high_yield", "bid_to_cover_ratio", "announcemt_date", "pdf_filenm_announcemt",
           "pdf_filenm_comp_results")
COLUMNS = ("auction_date", "close_comp_et", "close_comp_datetime_et", "close_comp_datetime_utc", "close_noncomp_et",
           "kind", "tenor", "tenor_rule", "small_value_test", "security_type", "security_term", "original_security_term", "reopening", "cusip",
           "issue_date", "maturity_date", "offering_amt", "comp_accepted", "primary_dealer_accepted",
           "direct_bidder_accepted", "indirect_bidder_accepted", "total_accepted", "soma_accepted", "high_yield",
           "bid_to_cover_ratio", "pd_share", "announcemt_date", "pdf_filenm_comp_results", "shared_day",
           "source_url", "method", "accessed_utc")


class GateError(AssertionError):
    pass


def gate(cond, msg):
    if not cond:
        raise GateError(msg)


# --------------------------------------------------------------------------- raw cache

def raw_dir() -> Path:
    return data_root() / "raw" / "treasury_auctions"


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    delay = 3.0
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code == 404:
                raise
            if attempt == 3:
                raise RuntimeError(f"GET {url} failed after 4 attempts: {type(exc).__name__}: {exc}") from exc
            time.sleep(delay)
            delay *= 2
    return b""


def _stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _iso(stamp):
    return f"{stamp[0:4]}-{stamp[4:6]}-{stamp[6:8]}T{stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]}Z"


def load_manifest(d: Path) -> dict:
    p = d / "_manifest.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_manifest(d: Path, man: dict):
    d.mkdir(parents=True, exist_ok=True)
    (d / "_manifest.json").write_text(json.dumps(man, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def acquire(d: Path, man: dict, key: str, url: str, log) -> dict:
    rec = man.get(key)
    if rec and (d / rec["path"]).exists():
        return rec
    st = _stamp()
    body = _get(url)
    path = f"{key}__{st}.json"
    d.mkdir(parents=True, exist_ok=True)
    (d / path).write_bytes(body)
    rec = {"url": url, "path": path, "method": "fetched", "accessed_utc": _iso(st), "bytes": len(body),
           "sha256": hashlib.sha256(body).hexdigest()}
    man[key] = rec
    save_manifest(d, man)
    log(f"    {key}: {len(body):,} bytes")
    time.sleep(PAUSE)
    return rec


def read_json(d: Path, rec: dict):
    body = (d / rec["path"]).read_bytes()
    assert hashlib.sha256(body).hexdigest() == rec["sha256"], f"sha256 mismatch on {rec['path']}"
    return json.loads(body.decode("utf-8"))


def fd_url(page: int) -> str:
    q = {"filter": FILTER, "page[size]": str(PAGE), "page[number]": str(page), "sort": "auction_date"}
    return API + "?" + urllib.parse.urlencode(q, safe=":,()")


# --------------------------------------------------------------------------- probe / fetch

def probe(log=print) -> int:
    url = API + "?" + urllib.parse.urlencode({"filter": FILTER, "page[size]": "1"}, safe=":,()")
    d = json.loads(_get(url).decode("utf-8"))
    log(f"  total-count {d['meta'].get('total-count')}, {len(d['meta']['labels'])} fields")
    missing = [c for c in COLS_FD if c not in d["meta"]["labels"]]
    log(f"  fields this builder needs and the API lacks: {missing}")
    return 0 if not missing else 1


def fd_pages(d: Path, man: dict, log) -> list[dict]:
    rec = acquire(d, man, "fd_page_0001", fd_url(1), log)
    first = read_json(d, rec)
    pages = int(first["meta"]["total-pages"])
    out = [rec]
    for p in range(2, pages + 1):
        out.append(acquire(d, man, f"fd_page_{p:04d}", fd_url(p), log))
    return out


def fetch(log=print) -> int:
    d = raw_dir()
    man = load_manifest(d)
    log("fetch: Fiscal Data auctions_query (Note, Bond; 2009-01-01 onward)")
    recs = fd_pages(d, man, log)
    rows, _ = parse_fd(d, recs)
    log(f"  {len(rows)} coupon rows parsed; G8 sample from TreasuryDirect")
    for cusip in sorted({r["cusip"] for r in g8_sample(rows)}):
        try:
            acquire(d, man, f"td_{cusip}", TD_SEARCH.format(cusip=cusip), log)
        except (RuntimeError, urllib.error.HTTPError) as exc:
            log(f"    td_{cusip}: FAILED ({type(exc).__name__}) -- recorded as not checkable")
    save_manifest(d, man)
    log(f"fetch done: {len(man)} raw responses in {d}")
    return 0


# --------------------------------------------------------------------------- build

def parse_clock(s: str | None) -> str | None:
    if not s:
        return None
    m = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*([AP])\.?M\.?\s*", s.upper())
    if not m:
        return None
    h, mi = int(m.group(1)) % 12, int(m.group(2))
    return f"{h + (12 if m.group(3) == 'P' else 0):02d}:{mi:02d}"


def _num(x):
    return None if x in (None, "", "null") else float(x)


def classify(rec: dict) -> tuple[str, str]:
    """(kind, tenor). The tenor is the term the auction was SOLD as:
    * a routine reopening carries its remaining term ('9-Year 10-Month') -> the ORIGINAL term (10y);
    * but Treasury has also met a standard auction by reopening an OLDER issue, and then `security_term` is itself a
      whole standard term that differs from the original: 2015-05-26 '2-Year' on a 5-year CUSIP, 2019-11-05 '3-Year'
      on a 10-year one, 2013-08-28 '5-Year' on a 7-year one (19 such rows 2013-2026). Those ARE the 2y/3y/5y auction
      of their month, so the tenor is `security_term`. Without this rule G2 fails in 11 tenor-years."""
    kind = "TIPS" if rec.get("inflation_index_security") == "Yes" else "FRN" if rec.get("floating_rate") == "Yes" \
        else "NOMINAL"
    ost, st = rec.get("original_security_term"), rec.get("security_term") or ""
    gate(ost in TENORS, f"G6: unknown original_security_term {ost!r} (cusip {rec.get('cusip')}, "
                        f"{rec.get('auction_date')}, {kind})")
    if re.fullmatch(r"\d+-Year", st) and st != ost:
        gate(st in TENORS, f"G6: unknown as-auctioned security_term {st!r} (cusip {rec.get('cusip')})")
        return kind, TENORS[st]
    return kind, TENORS[ost]


SMALL_VALUE_USD = 1e9   # Treasury's small-value contingency auctions ($25m: 2019-06-21 10y, 2021-12-02 20y); the
                        # paper excludes the 2019 one (SR 1188 fn. 10). Not a supply event: flagged, not counted.


def parse_fd(d: Path, recs: list[dict]) -> tuple[list[dict], list[dict]]:
    rows, not_sourced = [], []
    for rec in recs:
        for x in read_json(d, rec)["data"]:
            kind, tenor = classify(x)
            ad = x["auction_date"]
            clk = parse_clock(x.get("closing_time_comp"))
            if clk is None:
                not_sourced.append({"auction_date": ad, "cusip": x.get("cusip"), "kind": kind, "tenor": tenor,
                                    "closing_time_comp": x.get("closing_time_comp"), "source_url": rec["url"],
                                    "reason": "competitive close missing or unparsable; never assumed"})
                continue
            y, mo, dd = map(int, ad.split("-"))
            hh, mm = map(int, clk.split(":"))
            local = datetime(y, mo, dd, hh, mm, tzinfo=ET)
            ca, pd_ = _num(x.get("comp_accepted")), _num(x.get("primary_dealer_accepted"))
            row = {c: ("" if x.get(c) in (None, "null") else str(x.get(c))) for c in COLS_FD if c in COLUMNS}
            row.update({"auction_date": ad, "close_comp_et": clk, "close_comp_datetime_et": local.isoformat(),
                        "close_comp_datetime_utc": local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "close_noncomp_et": parse_clock(x.get("closing_time_noncomp")) or "",
                        "kind": kind, "tenor": tenor,
                        "tenor_rule": "original" if TENORS.get(x.get("original_security_term")) == tenor
                        else "as_auctioned",
                        "small_value_test": "True" if (_num(x.get("offering_amt")) or 0) < SMALL_VALUE_USD
                        and _num(x.get("offering_amt")) is not None else "False",
                        "pd_share": "" if not ca or pd_ is None else f"{pd_ / ca:.6f}",
                        "shared_day": "", "source_url": rec["url"], "method": "fetched",
                        "accessed_utc": rec["accessed_utc"]})
            rows.append(row)
    rows.sort(key=lambda r: (r["auction_date"], r["close_comp_et"], r["kind"], r["tenor"], r["cusip"]))
    return rows, not_sourced


def mark_shared(rows: list[dict]) -> dict:
    by_day: dict[str, list[dict]] = {}
    for r in rows:
        if r.get("small_value_test") == "True":
            continue                                    # a $25m contingency test is not a supply event
        by_day.setdefault(r["auction_date"], []).append(r)
    types: dict[str, list] = {}
    for day, rs in sorted(by_day.items()):
        if len(rs) < 2:
            continue
        for r in rs:
            r["shared_day"] = ";".join(f"{o['kind']}-{o['tenor']}@{o['close_comp_et']}" for o in rs if o is not r)
        kinds = sorted(o["kind"].lower() for o in rs)
        typ = "-".join(kinds)
        types.setdefault(typ, []).append({"date": day, "auctions": [f"{o['kind']} {o['tenor']} {o['close_comp_et']}"
                                                                     for o in rs]})
    return types


def g8_sample(rows: list[dict]) -> list[dict]:
    pool = sorted((r for r in rows if r["kind"] == "NOMINAL" and r.get("small_value_test") != "True"
                   and "2010-01-01" <= r["auction_date"] <= "2023-12-31"),
                  key=lambda r: (r["auction_date"], r["cusip"]))
    return random.Random(G8_SEED).sample(pool, min(G8_N, len(pool)))


def g8(rows: list[dict], td: dict[str, list | None]) -> dict:
    checked, clock_bad, listed, uncheckable = 0, [], [], []
    for r in g8_sample(rows):
        lst = td.get(r["cusip"])
        hit = [t for t in (lst or []) if str(t.get("auctionDate", ""))[:10] == r["auction_date"]]
        if not hit:
            uncheckable.append({"cusip": r["cusip"], "auction_date": r["auction_date"],
                                "reason": "not fetched" if lst is None else "no TreasuryDirect record on that date"})
            continue
        t = hit[0]
        checked += 1
        if parse_clock(t.get("closingTimeCompetitive")) != r["close_comp_et"]:
            clock_bad.append({"cusip": r["cusip"], "auction_date": r["auction_date"], "fiscal_data": r["close_comp_et"],
                              "treasurydirect": t.get("closingTimeCompetitive")})
        for fd_c, td_c in (("offering_amt", "offeringAmount"), ("primary_dealer_accepted", "primaryDealerAccepted")):
            a, b = _num(r[fd_c]), _num(t.get(td_c))
            if a != b:
                listed.append({"cusip": r["cusip"], "auction_date": r["auction_date"], "field": fd_c,
                               "fiscal_data": r[fd_c], "treasurydirect": t.get(td_c)})
    gate(not clock_bad, f"G8: the event clock disagrees between sources on {len(clock_bad)} auctions: {clock_bad[:2]}")
    gate(checked >= G8_MIN, f"G8: only {checked} of {G8_N} sampled auctions could be cross-checked (need {G8_MIN})")
    return {"sampled": G8_N, "checked": checked, "date_and_close_agree": checked, "amount_disagreements_listed": listed,
            "uncheckable": uncheckable, "pass": True}


def gates(rows: list[dict], not_sourced: list[dict], td: dict | None, asof: str, short_years=None) -> dict:
    short_years = SHORT_YEARS if short_years is None else short_years
    rep: dict = {}
    bad = [r for r in rows if not r["source_url"] or not r["accessed_utc"] or r["method"] != "fetched"]
    gate(not bad, f"G1: {len(bad)} rows without source_url, accessed_utc or method 'fetched'")
    rep["G1"] = {"rows": len(rows), "pass": True}
    keys = [(r["cusip"], r["auction_date"]) for r in rows]
    gate(len(keys) == len(set(keys)), "G4: duplicate (cusip, auction_date)")
    rep["G4"] = {"pass": True}
    counts: dict = {}
    for r in rows:
        if r["kind"] == "NOMINAL" and r.get("small_value_test") != "True":
            k = (r["tenor"], int(r["auction_date"][:4]))
            counts[k] = counts.get(k, 0) + 1
    off, named = {}, {}
    for t in NOMINAL_TENORS:
        for y in G2_YEARS:
            want = (0 if y < 2020 else 12) if t == "20y" else 12
            n = counts.get((t, y), 0)
            if n != want:
                if (t, y) in short_years:
                    named[f"{t} {y}"] = {"count": n, "reason": short_years[(t, y)]}
                else:
                    off[f"{t} {y}"] = n
    gate(not off, f"G2: nominal auctions a year outside the rule and not named: {off}")
    rep["G2"] = {"years": [G2_YEARS.start, G2_YEARS.stop - 1], "named_short_years": named, "pass": True}
    unparsed = [r for r in rows if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", r["close_comp_et"] or "")
                or parse_clock(_ampm(r["close_comp_et"])) != r["close_comp_et"]]
    gate(not unparsed, f"G3: {len(unparsed)} written rows whose close does not parse")
    unusual = [{"auction_date": r["auction_date"], "kind": r["kind"], "tenor": r["tenor"], "close": r["close_comp_et"]}
               for r in rows if r["close_comp_et"] not in USUAL_CLOSES]
    rep["G3"] = {"closes": _count(r["close_comp_et"] for r in rows), "unusual_closes_listed": unusual,
                 "not_sourced": len(not_sourced), "pass": True}
    for r in rows:
        if r["auction_date"] >= asof or not r["comp_accepted"]:
            continue
        ca = _num(r["comp_accepted"])
        gate(ca and ca > 0, f"G7: comp_accepted not > 0 on {r['cusip']} {r['auction_date']}")
        if r["pd_share"]:
            s = float(r["pd_share"])
            gate(0.0 <= s <= 1.0, f"G7: pd_share {s} outside [0, 1] on {r['cusip']} {r['auction_date']}")
    rep["G7"] = {"pass": True}
    if td is not None:
        rep["G8"] = g8(rows, td)
    return rep


def _ampm(hhmm: str) -> str:
    h, m = map(int, hhmm.split(":"))
    return f"{(h % 12) or 12}:{m:02d} {'PM' if h >= 12 else 'AM'}"


def _count(it) -> dict:
    out: dict = {}
    for x in it:
        out[x] = out.get(x, 0) + 1
    return dict(sorted(out.items()))


def build(log=print) -> int:
    t0 = time.time()
    d = raw_dir()
    man = load_manifest(d)
    fd_keys = sorted(k for k in man if k.startswith("fd_page_"))
    assert fd_keys, "no Fiscal Data pages cached; run --fetch first"
    recs = [man[k] for k in fd_keys]
    first = read_json(d, recs[0])
    assert int(first["meta"]["total-pages"]) == len(recs), "cached page count differs from the API's total-pages"
    total = int(first["meta"]["total-count"])
    rows, not_sourced = parse_fd(d, recs)
    gate(len(rows) + len(not_sourced) == total, f"rows {len(rows)} + not_sourced {len(not_sourced)} != total-count {total}")
    shared = mark_shared(rows)
    td = {}
    for r in g8_sample(rows):
        rec = man.get(f"td_{r['cusip']}")
        td[r["cusip"]] = read_json(d, rec) if rec else None
    asof = min(rec["accessed_utc"][:10] for rec in recs)
    rep = gates(rows, not_sourced, td, asof)
    rep["G5"] = {"shared_days_by_type": {k: len(v) for k, v in shared.items()}, "pass": True}
    per_tenor_year: dict = {}
    for r in rows:
        k = f"{r['kind']} {r['tenor']}"
        per_tenor_year.setdefault(k, {})
        y = r["auction_date"][:4]
        per_tenor_year[k][y] = per_tenor_year[k].get(y, 0) + 1
    meta = {
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "builder": "scripts/fetch_treasury_auctions.py", "record": "D710",
        "source": {"api": API, "filter": FILTER, "page_size": PAGE, "total_count": total,
                   "pages": [{k: man[key][k] for k in ("url", "accessed_utc", "bytes", "sha256")} for key in fd_keys]},
        "second_source_g8": {"api": TD_SEARCH, "responses": {k: {kk: v[kk] for kk in ("url", "accessed_utc", "bytes",
                             "sha256")} for k, v in sorted(man.items()) if k.startswith("td_")}},
        "span": {"from": rows[0]["auction_date"], "to": rows[-1]["auction_date"]},
        "rows": len(rows),
        "rows_per_kind_tenor_per_year": {k: dict(sorted(v.items())) for k, v in sorted(per_tenor_year.items())},
        "gates": rep,
        "shared_days": shared,
        "not_sourced": not_sourced,
        "conventions": {
            "tenor": "the ORIGINAL security term; a reopening's security_term is its remaining term",
            "close_comp_et": "closing_time_comp parsed to HH:MM, America/New_York; never assumed",
            "pd_share": "primary_dealer_accepted / comp_accepted; public at the results release",
            "shared_day": "the other Note/Bond auctions on the same date, as KIND-tenor@close",
            "future_rows": "the dataset carries announced auctions whose results are not yet published; their "
                           "amounts are empty. D710's runner cuts the file below 2024-01-01 at read.",
        },
    }
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows({c: r.get(c, "") for c in COLUMNS} for r in rows)
    OUT_META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    log(f"  wrote {OUT_CSV.relative_to(REPO)} ({len(rows)} rows) and {OUT_META.relative_to(REPO)} "
        f"in {time.time() - t0:.1f} s")
    log(f"  not_sourced {len(not_sourced)}; closes {rep['G3']['closes']}; unusual {len(rep['G3']['unusual_closes_listed'])}")
    log(f"  shared days by type {rep['G5']['shared_days_by_type']}")
    log(f"  G8 {rep['G8']['checked']}/{G8_N} checked, clock agrees on all; amount disagreements "
        f"{len(rep['G8']['amount_disagreements_listed'])}")
    return 0


# --------------------------------------------------------------------------- selftest

def _synthetic():
    rows = []
    for y in G2_YEARS:
        for m in range(1, 13):
            for i, t in enumerate(NOMINAL_TENORS):
                if t == "20y" and (y < 2020 or (y == 2020 and m < 5)):
                    continue
                ad = f"{y}-{m:02d}-{2 + i:02d}"
                rows.append({"auction_date": ad, "close_comp_et": "13:00", "kind": "NOMINAL", "tenor": t,
                             "cusip": f"C{t}{y}{m:02d}", "comp_accepted": "1000", "primary_dealer_accepted": "400",
                             "offering_amt": "1000", "pd_share": "0.400000", "source_url": "u", "method": "fetched",
                             "accessed_utc": "2026-09-30T00:00:00Z", "shared_day": ""})
    return rows


def expect(fn, g, what, log=print) -> int:
    try:
        fn()
    except GateError as e:
        assert str(e).startswith(g), f"{what}: raised at the wrong gate: {str(e)[:90]}"
        log(f"    {g} RAISES on {what}: {str(e)[:90]}")
        return 1
    raise AssertionError(f"{g} did not raise on {what}")


def selftest(log=print) -> int:
    log("selftest: every gate passes a clean case and RAISES on its own break")
    clean = _synthetic()
    sample = g8_sample(clean)
    td = {r["cusip"]: [{"auctionDate": r["auction_date"] + "T00:00:00", "closingTimeCompetitive": "01:00 PM",
                        "offeringAmount": "1000", "primaryDealerAccepted": "400"}] for r in sample}
    rep = gates(clean, [], td, "2030-01-01")
    assert rep["G8"]["checked"] == G8_N
    n = 0
    n += expect(lambda: gates([{**clean[0], "method": "inferred"}] + clean[1:], [], None, "2030-01-01"), "G1",
                "a row with method 'inferred'", log)
    n += expect(lambda: gates(clean + clean[:1], [], None, "2030-01-01"), "G4", "a duplicate (cusip, date)", log)
    n += expect(lambda: gates(clean[1:], [], None, "2030-01-01"), "G2", "a 2y year with 11 auctions, not named", log)
    gates(clean[1:], [], None, "2030-01-01", short_years={**SHORT_YEARS, ("2y", 2010): "named in the test"})
    log("    G2 passes the same short year once it is NAMED with a reason")
    n += expect(lambda: gates([{**clean[0], "close_comp_et": "1300"}] + clean[1:], [], None, "2030-01-01"), "G3",
                "a written close that does not parse", log)
    n += expect(lambda: gates([{**clean[0], "pd_share": "1.300000"}] + clean[1:], [], None, "2030-01-01"), "G7",
                "a primary-dealer share of 1.3", log)
    n += expect(lambda: classify({"original_security_term": "4-Year", "cusip": "X", "auction_date": "2015-01-01"}),
                "G6", "an unknown original term", log)
    base = {"inflation_index_security": "No", "floating_rate": "No", "cusip": "X", "auction_date": "2015-05-26"}
    assert classify({**base, "original_security_term": "5-Year", "security_term": "2-Year"}) == ("NOMINAL", "2y")
    assert classify({**base, "original_security_term": "10-Year", "security_term": "9-Year 10-Month"}) == ("NOMINAL", "10y")
    assert classify({**base, "original_security_term": "2-Year", "security_term": "1-Year 11-Month",
                     "floating_rate": "Yes"}) == ("FRN", "2y")
    log("    classify: a 5-year CUSIP sold as '2-Year' is the 2y auction; a '9-Year 10-Month' reopening is 10y; FRN kept")
    bad_td = {**td, sample[0]["cusip"]: [{**td[sample[0]["cusip"]][0], "closingTimeCompetitive": "11:30 AM"}]}
    n += expect(lambda: gates(clean, [], bad_td, "2030-01-01"), "G8", "TreasuryDirect giving another close", log)
    thin_td = {k: (v if i >= 3 else None) for i, (k, v) in enumerate(td.items())}
    n += expect(lambda: gates(clean, [], thin_td, "2030-01-01"), "G8", "only 21 of 24 checkable", log)
    amt_td = {**td, sample[1]["cusip"]: [{**td[sample[1]["cusip"]][0], "offeringAmount": "999"}]}
    r8 = gates(clean, [], amt_td, "2030-01-01")["G8"]
    assert len(r8["amount_disagreements_listed"]) == 1
    log("    G8 LISTS an offering-amount disagreement without raising or overwriting")
    two = [{**clean[0]}, {**clean[0], "cusip": "OTHER", "kind": "TIPS", "tenor": "10y", "close_comp_et": "11:30"}]
    types = mark_shared(two)
    assert list(types) == ["nominal-tips"] and "TIPS-10y@11:30" in two[0]["shared_day"]
    log("    G5 names a nominal-TIPS shared day and marks both rows")
    assert parse_clock("01:00 PM") == "13:00" and parse_clock("11:30 AM") == "11:30" and parse_clock("12:00 PM") == "12:00"
    assert parse_clock(None) is None and parse_clock("TBD") is None
    log("    parse_clock: 01:00 PM -> 13:00, 11:30 AM -> 11:30, 12:00 PM -> 12:00; missing -> None (not_sourced)")
    assert n == 8
    log(f"selftest: PASS ({n} breaks raised at their own gates)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for f in ("probe", "fetch", "build", "selftest"):
        ap.add_argument(f"--{f}", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.probe:
        return probe()
    if a.fetch:
        return fetch()
    if a.build:
        return build()
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
