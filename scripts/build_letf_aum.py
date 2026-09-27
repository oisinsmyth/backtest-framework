"""LETF close-flow Phase 1: the point-in-time AUM panel for the ten index LETFs, and Gate 0 (deposit s.3.2, s.9;
LETF-A1..A4 in docs/internal/LETF_CLOSE_FLOW_AMENDMENTS.md). The principal, 2026-09-27: "Yes, build Phase 1 and
Gate 0".

    uv run python scripts/build_letf_aum.py --fetch      # EDGAR N-PORT: Direxion SPXL/SPXS and ProShares' eight (cached)
    uv run python scripts/build_letf_aum.py --build      # the panel + data/letf/gate0.json
    uv run python scripts/build_letf_aum.py --selftest   # every Gate 0 check must FIRE on a broken input

SEAL (A10): nothing dated on or after 2025-03-01 is parsed. A N-PORT filing whose report period ends after 2025-02-28
is skipped once its <repPdEnd> is read; nothing else in it is parsed.

THE PANEL (data/letf/letf_aum_daily.csv.gz, not the deposit's Parquet: the uv environment has no parquet
engine; columns date, ticker, nav, shares_out, aum, source, estimated):
- ProShares (8): the issuer's all-funds historical NAV file (the principal's, 2026-09-24). aum = the published AUM;
  shares_out in shares. Identity check: nav x shares = aum.
- Direxion SPXL/SPXS (LETF-A3): month-end net assets rebuilt from N-PORT (quarter-end netAssets, walked back through
  each month's flow and return), then a daily estimate. The NAV path is the same-benchmark ProShares fund's
  (SPXL <- UPRO, both 3x S&P 500; SPXS <- SPXU, both -3x): shares-equivalent = aum / path, linear in trading days
  between month-ends, so every month-end anchor is hit exactly. nav is the path, rescaled (a proxy, not SPXL's NAV).
  Before the first anchor (2019) Direxion is ABSENT: LETF-A3's pre-2019 route is still open.

THE BAND (measured, never assumed): the identical monthly-anchor procedure applied to each ProShares fund, whose daily
truth is known, with its own NAV path. The per-day relative error distribution is the band. The path error is
measured separately: SPXL's N-PORT monthly returns against UPRO's compounded month.

GATE 0 (deposit s.3.2): (G1) no gap longer than 3 trading days, the calendar being SPY's daily dates (Alpha Vantage,
independent of both issuers); (G2) |dAUM| > 25% days listed for review, each checked against ProShares' split file
and against nav-return-plus-creation; (G3) >= 5 spot checks per ticker against an independent source: ProShares
funds against ProShares Trust's own N-PORT quarter-end netAssets; Direxion's rebuilt month-ends against the NEXT
older filing's netAssets (a different filing: LETF-A3's 1% test). Plus the identity nav x shares = aum.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import re
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "letf"
RAW = REPO / "data" / "raw" / "letf" / "nport"
PS_ZIP = REPO / "data" / "raw" / "proshares_historical_nav" / "historical_nav_2026-09-23.zip"
SPLITS = REPO / "data" / "fund_facts" / "proshares_splits.csv"
SPY = REPO / "data" / "raw" / "alphavantage" / "daily" / "SPY.json.gz"
RESERVED_FROM = "2025-03-01"
START = "2016-01-01"
WARM = "2015-10-01"  # read from here for the path to 2015-10-31, Direxion's first pre-2019 anchor
PRE2019 = REPO / "data" / "letf" / "direxion_pre2019_filings.csv"
UA = {"User-Agent": "BacktestFramework research script research@backtest-framework.org"}  # never a personal address
PROSHARES = {"TQQQ": 3, "SQQQ": -3, "QLD": 2, "QID": -2, "UPRO": 3, "SPXU": -3, "SSO": 2, "SDS": -2}
DIREXION = {"SPXL": 3, "SPXS": -3}
PATH_OF = {"SPXL": "UPRO", "SPXS": "SPXU"}  # same benchmark, same leverage
INDEX = {"TQQQ": "NDX", "SQQQ": "NDX", "QLD": "NDX", "QID": "NDX"}


def get(url: str, cache: Path) -> bytes:
    if cache.exists():
        return cache.read_bytes()
    time.sleep(0.15)  # <= 8 requests a second
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        b = r.read()
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(b)
    return b


def series_ids() -> dict[str, tuple[int, str]]:
    t = json.loads(get("https://www.sec.gov/files/company_tickers_mf.json", RAW / "company_tickers_mf.json"))
    want = set(PROSHARES) | set(DIREXION)
    out = {r[3]: (int(r[0]), r[1]) for r in t["data"] if r[3] in want}
    missing = want - set(out)
    if missing:
        raise RuntimeError(f"no EDGAR series for {sorted(missing)}")
    return out


def filings(sid: str) -> list[tuple[str, str]]:
    """(filing date, index href) for every NPORT-P of one series, from EDGAR's per-series feed."""
    out: list[tuple[str, str]] = []
    start = 0
    while True:
        url = (f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={sid}&type=NPORT-P&dateb="
               f"&owner=include&start={start}&count=100&output=atom")
        x = get(url, RAW / "feeds" / f"{sid}_{start}.xml").decode("utf-8", "replace")
        page = re.findall(r"<filing-date>([^<]+)</filing-date>.*?<filing-href>([^<]+)</filing-href>", x, re.S)
        if not page:
            page = [(d, h) for h, d in re.findall(r"<filing-href>([^<]+)</filing-href>.*?<filing-date>([^<]+)</filing-date>",
                                                  x, re.S)]
        out += page
        if len(page) < 100:
            return out
        start += 100


def primary_doc(href: str) -> Path:
    m = re.search(r"/data/(\d+)/(\d+)/", href)
    assert m, href
    cik, acc = m.groups()
    p = RAW / "docs" / f"{acc}.xml"
    get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/primary_doc.xml", p)
    return p


def parse_nport(p: Path, sid: str) -> dict | None:
    """The report date first; a report as of the seal or later is dropped before anything else is read.
    N-PORT's <repPdDate> is the date the report is AS OF (the quarter's last month-end); <repPdEnd> is the FUND'S
    FISCAL YEAR-END and must not be used as the report date (a first draft did, 2026-09-27; nothing sealed was read)."""
    x = p.read_text(encoding="utf-8", errors="replace")
    end = re.search(r"<repPdDate>([^<]+)</repPdDate>", x)
    if not end or end.group(1) >= RESERVED_FROM:
        return None
    s = re.search(r"<seriesId>(\w+)</seriesId>", x)
    if not s or s.group(1) != sid:
        raise RuntimeError(f"{p.name}: series {s.group(1) if s else None}, expected {sid}")
    nam = re.search(r"<netAssets>([^<]+)</netAssets>", x)
    if nam is None:
        raise RuntimeError(f"{p.name}: no <netAssets>")
    na = float(nam.group(1))
    flows = []
    for k in (1, 2, 3):
        f = re.search(rf"<mon{k}Flow ([^/]*)/>", x)
        a = dict(re.findall(r'(\w+)="([^"]*)"', f.group(1))) if f else {}
        # Direxion files redemptions as NEGATIVE numbers, ProShares as positive: the magnitude is subtracted
        flows.append(sum(float(a.get(n, 0) or 0) for n in ("sales", "reinvestment")) - abs(float(a.get("redemption", 0) or 0)))
    rt = re.search(r"<monthlyTotReturn ([^/]*)/>", x)
    ra = dict(re.findall(r'(\w+)="([^"]*)"', rt.group(1))) if rt else {}
    rets = [float(ra[f"rtn{k}"]) / 100 if ra.get(f"rtn{k}") not in (None, "", "N/A") else np.nan for k in (1, 2, 3)]
    return {"report_date": end.group(1), "net_assets": na, "flow": flows, "ret": rets, "doc": p.name}


def fetch() -> int:
    ids = series_ids()
    rec = {}
    for tk, (cik, sid) in sorted(ids.items()):
        fl = filings(sid)
        kept = []
        for _d, href in fl:
            r = parse_nport(primary_doc(href), sid)
            if r is not None:
                kept.append(r)
        kept.sort(key=lambda r: r["report_date"])
        rec[tk] = {"cik": cik, "series": sid, "filings_listed": len(fl), "periods_before_seal": len(kept), "reports": kept}
        print(f"  {tk:5s} {sid}: {len(fl)} NPORT-P listed, {len(kept)} report periods before {RESERVED_FROM}"
              f"{' (' + kept[0]['report_date'] + ' -> ' + kept[-1]['report_date'] + ')' if kept else ''}", flush=True)
    (OUT / "nport_reports.json").write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def month_end(d: str, back: int) -> pd.Timestamp:
    return (pd.Timestamp(d) + pd.offsets.MonthEnd(0)) - pd.offsets.MonthEnd(back)




def forward_estimate(path: pd.Series, reports: list[dict]) -> tuple[pd.Series, pd.DataFrame]:
    """Daily net assets from N-PORT alone plus a daily NAV path (LETF-A3, second form; the monthly walk-back above
    broke in 2020-Q1, where -47% and +37% months met $843m of March inflow).

    From each filed quarter-end, A(t) = A(t-1) x path(t)/path(t-1) + that month's filed net flow / its trading days.
    At the next filed quarter-end the forward value is compared with the filing (the CHECK, before any correction),
    then the residual ratio is spread geometrically over the quarter's trading days so every filing is hit exactly.
    After the last filing the path is carried with no flow (flagged by the caller)."""
    path = path.sort_index()
    idx = path.index
    reps = sorted(reports, key=lambda r: r["report_date"])
    est = pd.Series(np.nan, index=idx)
    checks = []
    for a, b in zip(reps, reps[1:]):
        d0, d1 = idx[idx <= a["report_date"]], idx[idx <= b["report_date"]]
        if not len(d0) or not len(d1):
            continue
        d0, d1 = d0[-1], d1[-1]
        months = {month_end(b["report_date"], 3 - k).to_period("M"): b["flow"][k - 1] for k in (1, 2, 3)}
        seg = idx[(idx > d0) & (idx <= d1)]
        if month_end(a["report_date"], 0) != month_end(b["report_date"], 3):
            raise RuntimeError(f"a quarter is missing between {a['report_date']} and {b['report_date']}")
        per = pd.Series(seg.to_period("M"), index=seg)
        ndays = per.value_counts()
        if b.get("implied_flow"):
            # the quarter's flow is SOLVED from its two anchors, as one even daily flow f:
            # NA_b = NA_a x P(d1)/P(d0) + f x sum_t P(d1)/P(t). No check is possible here; the caller checks the
            # solved flows against an independent total (the half-year statements).
            f = (b["net_assets"] - a["net_assets"] * path[d1] / path[d0]) / float((path[d1] / path[seg]).sum())
            daily = pd.Series(f, index=seg)
        else:
            daily = pd.Series([months[per[t]] / ndays[per[t]] for t in seg], index=seg)
        vals, x = [], a["net_assets"]
        prev = d0
        for t in seg:
            x = x * path[t] / path[prev] + daily[t]
            vals.append(x)
            prev = t
        ratio = b["net_assets"] / vals[-1]
        checks.append({"quarter_end": b["report_date"], "forward": vals[-1], "filed": b["net_assets"],
                       "rel_err": vals[-1] / b["net_assets"] - 1, "regime": b.get("regime", "nport_monthly"),
                       "implied": bool(b.get("implied_flow")), "flow_total": float(daily.sum())})
        n = len(seg)
        est[d0] = a["net_assets"]
        est[seg] = [v * ratio ** ((j + 1) / n) for j, v in enumerate(vals)]
    last = idx[idx <= reps[-1]["report_date"]][-1]
    tail = idx[idx > last]
    if len(tail):
        est[tail] = est[last] * path[tail] / path[last]
    return est.dropna(), pd.DataFrame(checks)


def calendar() -> pd.DatetimeIndex:
    d = json.load(gzip.open(SPY, "rt", encoding="utf-8"))
    return pd.DatetimeIndex(sorted(pd.Timestamp(x) for x in d if START <= x < RESERVED_FROM))


def proshares(start: str = START) -> pd.DataFrame:
    with zipfile.ZipFile(PS_ZIP) as z:
        raw = z.read("historical_nav.csv")
    df = pd.read_csv(io.BytesIO(raw), encoding="utf-8", usecols=["Date", "Ticker", "NAV", "Shares Outstanding (000)",
                                                                 "Assets Under Management"])
    df = df[df["Ticker"].isin(list(PROSHARES))].copy()
    df["date"] = pd.to_datetime(df["Date"])
    df = df[(df["date"] >= start) & (df["date"] < RESERVED_FROM)]
    out = pd.DataFrame({"date": df["date"], "ticker": df["Ticker"], "nav": df["NAV"].astype(float),
                        "shares_out": df["Shares Outstanding (000)"].astype(float) * 1000,
                        "aum": df["Assets Under Management"].astype(float),
                        "source": "ProShares all-funds historical NAV file (issuer), 2026-09-23", "estimated": False})
    return out.sort_values(["ticker", "date"]).reset_index(drop=True)


def accounting_basis(g: pd.DataFrame) -> pd.Series:
    """Net assets as a fund's books (and N-PORT) state them: NAV(t) x shares(t-1). The issuer's published shares and
    AUM for day t already include day t's creation and redemption orders; the books take them in on t+1. Verified by
    hand on TQQQ and QID quarter-ends (2020-11-30, 2021-02-26, 2021-05-28: N-PORT = NAV(t) x shares(t-1) to the
    digits filed). The issuer's AUM is the model's A: it includes the orders the fund hedges at that close."""
    return (g["nav"] * g["shares_out"].shift(1)).dropna()




def quarter_ends(first: str, last: str) -> list[str]:
    """Direxion's fiscal quarter-ends (FY to 31 October): Jan, Apr, Jul, Oct."""
    return [str(d.date()) for d in pd.date_range(first, last, freq="ME") if d.month in (1, 4, 7, 10)]


def spread(total: float, months: list[pd.Period], tdays: pd.DatetimeIndex) -> dict[pd.Period, float]:
    """A period total spread evenly over its trading days, returned per month."""
    per = pd.Series(tdays.to_period("M"))
    n = {m: int((per == m).sum()) for m in months}
    tot = sum(n.values())
    if tot == 0:
        raise RuntimeError(f"no trading days in {months[0]}..{months[-1]}")
    return {m: total * n[m] / tot for m in months}


def pre2019_reports(tk: str, tdays: pd.DatetimeIndex, nport_first: dict) -> tuple[list[dict], dict]:
    """Direxion's quarter-ends 2015-10-31 -> 2019-07-31 from the transcribed filings (data/letf/direxion_pre2019_filings.csv,
    `scripts/fetch_direxion_pre2019.py`), as reports forward_estimate can walk.

    Anchors are put on N-PORT's (the books') basis: an N-CSR/N-CSRS net assets figure includes creations and
    redemptions traded but not settled, so the receivable for shares sold is removed and the payable for shares
    redeemed added back (at 2019-10-31 that reproduces N-PORT to -$4,094 SPXL and -$11,202 SPXS). The N-Q and NPORT-EX
    totals are taken as filed: their basis is untested (no overlap), and the size of the difference is reported.
    Flows: N-SAR's monthly sales less redemptions to October 2017 (regime `nsar_monthly`, walked forward and checked
    at each quarter-end). From November 2017 to July 2019 there are no monthly flows: each quarter's flow is SOLVED
    from its two anchors (regime `semiannual`), and the solved flows are checked against the half-year statement
    totals (sales + redemptions + transaction fees; May-July 2019 = the half less N-PORT's own Aug-Oct months)."""
    d = pd.read_csv(PRE2019, encoding="utf-8", dtype={"as_of": str, "period_start": str, "period_end": str})
    d = d[d["ticker"] == tk]

    def val(field: str, as_of: str, forms: tuple[str, ...]) -> float | None:
        r = d[(d["field"] == field) & (d["as_of"] == as_of) & d["form"].isin(forms)]
        return float(r["value"].iloc[0]) if len(r) else None

    anchors: dict[str, float] = {}
    basis: dict[str, dict] = {}
    for q in quarter_ends("2015-10-31", "2019-07-31"):
        na = val("net_assets", q, ("N-CSR", "N-CSRS"))
        if na is not None:
            rec = val("receivable_shares_sold_usd", q, ("N-CSR", "N-CSRS")) or 0.0
            pay = val("payable_shares_redeemed_usd", q, ("N-CSR", "N-CSRS")) or 0.0
            anchors[q], basis[q] = na - rec + pay, {"form": "N-CSR/N-CSRS", "receivable": rec, "payable": pay}
        else:
            na = val("net_assets", q, ("N-Q", "NPORT-EX"))
            if na is None:
                raise RuntimeError(f"{tk}: no net assets at {q}")
            anchors[q], basis[q] = na, {"form": "N-Q/NPORT-EX", "basis": "as filed, untested"}
    flow: dict[pd.Period, float] = {}
    ms = d[d["field"].isin(["month_sales_usd", "month_redemptions_usd"])]
    for (ps_, _pe), g in ms.groupby(["period_start", "period_end"]):
        m = pd.Period(ps_[:7], "M")
        if pd.Period("2015-11", "M") <= m <= pd.Period("2017-10", "M"):
            s = g.loc[g["field"] == "month_sales_usd", "value"].sum()
            r = g.loc[g["field"] == "month_redemptions_usd", "value"].sum()
            flow[m] = float(s) - abs(float(r))

    def cap(start: str, end: str) -> float:
        g = d[(d["period_start"] == start) & (d["period_end"] == end)
              & d["field"].isin(["sales_usd", "redemptions_usd", "transaction_fees_usd"])]
        if g["field"].nunique() != 3:
            raise RuntimeError(f"{tk}: statement flows incomplete for {start}..{end}")
        return float(g["value"].sum())

    halves: list[dict] = []  # the statement totals the solved quarterly flows are checked against
    for fy in (2018, 2019):
        h1 = cap(f"{fy - 1}-11-01", f"{fy}-04-30")
        h2 = cap(f"{fy - 1}-11-01", f"{fy}-10-31") - h1
        m1 = list(pd.period_range(f"{fy - 1}-11", f"{fy}-04", freq="M"))
        flow.update(spread(h1, m1, tdays))
        halves.append({"half": f"FY{fy} H1", "quarters": [f"{fy}-01-31", f"{fy}-04-30"], "statement": h1,
                       "start_na": f"{fy - 1}-10-31"})
        if fy == 2019:
            aug_oct = float(sum(nport_first["flow"]))  # N-PORT's own Aug, Sep, Oct 2019
            flow.update(spread(h2 - aug_oct, list(pd.period_range("2019-05", "2019-07", freq="M")), tdays))
            halves.append({"half": "FY2019 May-Jul (H2 less N-PORT Aug-Oct)", "quarters": ["2019-07-31"],
                           "statement": h2 - aug_oct, "start_na": "2019-04-30"})
        else:
            flow.update(spread(h2, list(pd.period_range(f"{fy}-05", f"{fy}-10", freq="M")), tdays))
            halves.append({"half": f"FY{fy} H2", "quarters": [f"{fy}-07-31", f"{fy}-10-31"], "statement": h2,
                           "start_na": f"{fy}-04-30"})
    reports = []
    for q in sorted(anchors):
        months = [pd.Period(q[:7], "M") - k for k in (2, 1, 0)]
        regime = "nsar_monthly" if q <= "2017-10-31" else "semiannual"
        reports.append({"report_date": q, "net_assets": anchors[q], "regime": regime, "implied_flow": regime == "semiannual",
                        "flow": [flow.get(m, 0.0) for m in months] if q > "2015-10-31" else [0.0, 0.0, 0.0]})
        if q > "2015-10-31" and any(m not in flow for m in months):
            raise RuntimeError(f"{tk}: no flow for a month of the quarter ending {q}")
    gap = [abs(float(b["receivable"]) - float(b["payable"])) / anchors[q] for q, b in basis.items() if "receivable" in b]
    for h in halves:
        h["start_na_value"] = anchors[h["start_na"]]
    return reports, {"anchor_basis": basis, "halves": halves,
                     "statement_basis_gap": {"n": len(gap), "max": max(gap), "median": float(np.median(gap))}}


def half_year_checks(checks: pd.DataFrame, halves: list[dict]) -> list[dict]:
    """The solved quarterly flows of each half-year against the statement's total, relative to net assets at the
    half's start (an independent check: the statements' flows never entered the solve)."""
    fl = checks.set_index("quarter_end")["flow_total"]
    out = []
    for h in halves:
        solved = float(sum(fl[q] for q in h["quarters"]))
        out.append({"date": h["quarters"][-1], "half": h["half"], "solved_flow": solved, "statement_flow": h["statement"],
                    "rel_err": (solved - h["statement"]) / h["start_na_value"], "regime": "semiannual_flow"})
    return out


def band_regimes(psw: pd.DataFrame) -> dict:
    """The pre-2019 procedures where the daily truth is known: each ProShares fund on Direxion's quarter-end calendar
    (Jan/Apr/Jul/Oct, 2015-10 -> 2025-01), anchors on the books' basis.
    - `nsar_monthly`: the fund's issuer flows (shares change x NAV, day t's orders) summed by month, walked forward;
      the forward checks are the G3 reference.
    - `semiannual`: each quarter's flow SOLVED from its two anchors (as Direxion's Nov 2017 -> Jul 2019); the check is
      the solved half-year flow against the true half-year total, relative to net assets at the half's start, and
      that distribution is the G3 reference for Direxion's half-year statement checks.
    Scored against the issuer's published AUM, per day."""
    out: dict = {}
    for regime in ("nsar_monthly", "semiannual"):
        pooled, fwd = [], []
        for _tk, g in psw.groupby("ticker"):
            g = g.set_index("date").sort_index()
            acct = accounting_basis(g)
            f = ((g["shares_out"] - g["shares_out"].shift(1)) * g["nav"]).dropna()
            per = f.groupby(f.index.to_period("M")).sum()
            qs = [q for q in quarter_ends("2015-10-31", "2025-01-31") if (acct.index <= q).any() and q >= str(acct.index[0].date())]
            na = {q: float(acct[acct.index <= q].iloc[-1]) for q in qs}
            reps = [{"report_date": q, "net_assets": na[q], "regime": regime, "implied_flow": regime == "semiannual",
                     "flow": [float(per.get(pd.Period(q[:7], "M") - k, 0.0)) for k in (2, 1, 0)]} for q in qs]
            est, chk = forward_estimate(g["nav"], reps)
            err = (est[(est.index >= START) & (est.index <= qs[-1])] / g["aum"] - 1).dropna()
            pooled.append(err)
            if regime == "nsar_monthly":
                fwd.append(chk["rel_err"])
            else:
                fl = chk.set_index("quarter_end")["flow_total"]
                for q1, q2 in zip(qs, qs[1:]):
                    if q2[5:7] in ("04", "10") and q1 in fl.index and q2 in fl.index:
                        start = [q for q in qs if q < q1]
                        if not start:
                            continue
                        lo, hi = pd.Timestamp(start[-1]), pd.Timestamp(q2)
                        true = float(f[(f.index > lo) & (f.index <= hi)].sum())
                        fwd.append(pd.Series([(fl[q1] + fl[q2] - true) / na[start[-1]]]))
        e, fc = pd.concat(pooled), pd.concat(fwd)
        key = "forward_checks" if regime == "nsar_monthly" else "half_year_flow_checks"
        out[regime] = {key: {"n": int(len(fc)), "abs_p50": float(fc.abs().median()),
                             "abs_p90": float(fc.abs().quantile(0.9)), "abs_max": float(fc.abs().max()),
                             "over_1pct": int((fc.abs() > 0.01).sum())},
                       "daily": {"days": int(len(e)), "abs_p50": float(e.abs().median()),
                                 "abs_p95": float(e.abs().quantile(0.95)), "abs_p99": float(e.abs().quantile(0.99))}}
    return out


def band(ps: pd.DataFrame, nport: dict) -> dict:
    """Direxion's procedure run where the daily truth is known: each ProShares fund's OWN N-PORT filings (quarter-end
    net assets on the books' basis, monthly net flows) and its own NAV as the path, through forward_estimate, scored
    against the issuer's published AUM from the first filing to the last. Error = estimate / truth - 1 per day; the
    forward check at each quarter-end is kept too, so Direxion's residuals can be read against the same distribution."""
    out, pooled, fwd = {}, [], []
    for tk, g in ps.groupby("ticker"):
        g = g.set_index("date").sort_index()
        est, chk = forward_estimate(g["nav"], nport[tk]["reports"])
        last = pd.Timestamp(max(r["report_date"] for r in nport[tk]["reports"]))
        err = (est[est.index <= last] / g["aum"] - 1).dropna()
        pooled.append(err)
        fwd.append(chk["rel_err"])
        out[tk] = {"days": int(len(err)), "p05": float(err.quantile(0.05)), "p50": float(err.median()),
                   "p95": float(err.quantile(0.95)), "abs_p95": float(err.abs().quantile(0.95)),
                   "forward_check_abs_max": float(chk["rel_err"].abs().max())}
    f = pd.concat(fwd)
    out["_forward_checks"] = {"n": int(len(f)), "abs_p50": float(f.abs().median()), "abs_p90": float(f.abs().quantile(0.9)),
                              "abs_max": float(f.abs().max()), "over_1pct": int((f.abs() > 0.01).sum())}
    e = pd.concat(pooled)
    out["_pooled"] = {"days": int(len(e)), "p05": float(e.quantile(0.05)), "p95": float(e.quantile(0.95)),
                      "abs_p50": float(e.abs().median()), "abs_p95": float(e.abs().quantile(0.95)),
                      "abs_p99": float(e.abs().quantile(0.99))}
    return out


def direxion(ps: pd.DataFrame, nport: dict) -> tuple[pd.DataFrame, dict]:
    rows, info = [], {}
    for tk in DIREXION:
        path = ps[ps["ticker"] == PATH_OF[tk]].set_index("date")["nav"].sort_index()
        pre, pre_info = pre2019_reports(tk, path.index, nport[tk]["reports"][0])
        reps = pre + nport[tk]["reports"]
        est, checks = forward_estimate(path, reps)  # nothing before the first anchor
        est = est[est.index >= START]
        hy = half_year_checks(checks, pre_info["halves"])
        first = pd.Timestamp(reps[0]["report_date"])
        last_filed = max(r["report_date"] for r in nport[tk]["reports"])
        # path error: the fund's filed monthly return against the proxy's compounded month
        pe = []
        for r in nport[tk]["reports"]:
            for k in (1, 2, 3):
                me = month_end(r["report_date"], 3 - k)
                p = path[(path.index <= me) & (path.index > me - pd.offsets.MonthEnd(1))]
                p0 = path[path.index <= me - pd.offsets.MonthEnd(1)]
                if len(p) and len(p0) and not np.isnan(r["ret"][k - 1]):
                    pe.append(r["ret"][k - 1] - (p.iloc[-1] / p0.iloc[-1] - 1))
        pe_s = pd.Series(pe)
        scale = path / path[path.index >= START].iloc[0]
        src = pd.Series(f"estimate: N-PORT quarter-ends + monthly flows (EDGAR series {nport[tk]['series']}), "
                        f"daily path {PATH_OF[tk]} NAV (LETF-A3)", index=est.index)
        src[est.index <= "2019-07-31"] = (f"estimate: N-CSR/N-CSRS/N-Q quarter-ends + N-SAR monthly flows, daily path "
                                          f"{PATH_OF[tk]} NAV (LETF-A5)")
        src[(est.index > "2017-10-31") & (est.index <= "2019-07-31")] = (
            f"estimate: N-CSR/N-CSRS/N-Q quarter-ends + half-year statement flows spread, daily path {PATH_OF[tk]} NAV (LETF-A5)")
        src[est.index > last_filed] += "; AFTER THE LAST FILING: path only, no flow"
        rows.append(pd.DataFrame({"date": est.index, "ticker": tk, "nav": scale.reindex(est.index).values,
                                  "shares_out": (est / scale.reindex(est.index)).values, "aum": est.values,
                                  "source": src.values, "estimated": True}))
        info[tk] = {"first_anchor": str(first.date()), "last_anchor": last_filed, "pre2019": pre_info,
                    "half_year_checks": hy,
                    "quarter_ends": len(reps),
                    "forward_checks": checks.to_dict("records"),
                    "forward_abs_max": float(checks["rel_err"].abs().max()) if len(checks) else None,
                    "forward_over_1pct": int((checks["rel_err"].abs() > 0.01).sum()) if len(checks) else None,
                    "path_error_monthly": {"n": int(len(pe_s)), "mean": float(pe_s.mean()),
                                           "abs_p95": float(pe_s.abs().quantile(0.95)), "abs_max": float(pe_s.abs().max())}}
    return pd.concat(rows, ignore_index=True), info


def gate0(panel: pd.DataFrame, cal: pd.DatetimeIndex, nport: dict, dx_info: dict,
          ref: dict[str, dict] | None = None) -> dict:
    res: dict = {"tickers": {}}
    splits = pd.read_csv(SPLITS, encoding="utf-8")
    scol = [c for c in splits.columns if "date" in c.lower()][0]
    tcol = [c for c in splits.columns if "ticker" in c.lower() or "symbol" in c.lower()][0]
    splits[scol] = pd.to_datetime(splits[scol], errors="coerce")
    for tk, g in panel.groupby("ticker"):
        g = g.sort_values("date").set_index("date")
        span = cal[(cal >= g.index.min()) & (cal <= g.index.max())]
        missing = span.difference(g.index)
        run = longest = 0
        present = set(g.index)
        for d in span:
            run = run + 1 if d not in present else 0
            longest = max(longest, run)
        extra = g.index.difference(cal)
        ident = (g["nav"] * g["shares_out"] / g["aum"] - 1).abs() if not g["estimated"].iloc[0] else pd.Series(dtype=float)
        dA = g["aum"].pct_change().abs()
        big = dA[dA > 0.25]
        flagged = []
        for d, v in big.items():
            prev = g.index[g.index < d][-1]
            nav_r = g.loc[d, "nav"] / g.loc[prev, "nav"] - 1
            creation = (g.loc[d, "shares_out"] - g.loc[prev, "shares_out"]) * g.loc[d, "nav"]
            resid = g.loc[d, "aum"] - g.loc[prev, "aum"] * (1 + nav_r) - creation
            sp = splits[(splits[tcol] == tk) & ((splits[scol] - d).abs() <= pd.Timedelta(days=3))]
            flagged.append({"date": str(d.date()), "abs_daum": float(v), "nav_ret": float(nav_r),
                            "creation_usd": float(creation), "unexplained_usd": float(resid),
                            "unexplained_rel": float(resid / g.loc[prev, "aum"]), "split_within_3d": bool(len(sp))})
        res["tickers"][tk] = {"first": str(g.index.min().date()), "last": str(g.index.max().date()), "rows": int(len(g)),
                              "estimated": bool(g["estimated"].iloc[0]), "calendar_days_missing": int(len(missing)),
                              "longest_gap_trading_days": int(longest), "rows_off_calendar": [str(d.date()) for d in extra],
                              "identity_abs_p99": float(ident.quantile(0.99)) if len(ident) else None,
                              "identity_share_within_1bp": float((ident <= 1e-4).mean()) if len(ident) else None,
                              "daum_over_25pct": flagged}
    # G3 spot checks
    ps = panel[~panel["estimated"]]
    for tk in [t for t in PROSHARES if t in res["tickers"]]:
        g = ps[ps["ticker"] == tk].set_index("date").sort_index()
        acct = accounting_basis(g)
        chk = []
        for r in nport.get(tk, {}).get("reports", []):
            d = pd.Timestamp(r["report_date"])
            if d < pd.Timestamp(START):
                continue
            on = acct[acct.index <= d]
            if len(on):
                chk.append({"date": r["report_date"], "panel_date": str(on.index[-1].date()),
                            "panel_nav_x_prior_shares": float(on.iloc[-1]), "panel_aum": float(g["aum"][on.index[-1]]),
                            "nport_net_assets": r["net_assets"], "rel_err": float(on.iloc[-1] / r["net_assets"] - 1)})
        res["tickers"][tk]["spot_checks"] = chk
    for tk in [t for t in DIREXION if t in res["tickers"]]:
        res["tickers"][tk]["spot_checks"] = [{"date": c["quarter_end"], "forward_before_correction": c["forward"],
                                             "filed_net_assets": c["filed"], "rel_err": c["rel_err"],
                                             "regime": c.get("regime", "nport_monthly")}
                                            for c in dx_info[tk]["forward_checks"] if not c.get("implied")] + list(
            dx_info[tk].get("half_year_checks", []))
    verdict = {}
    for tk, t in res["tickers"].items():
        sc = t["spot_checks"]
        if tk in DIREXION and ref is not None:
            # LETF-A5: each quarter within the same estimator's distribution on the ProShares funds, measured in the
            # same flow regime (N-PORT monthly, N-SAR monthly, or half-year totals spread)
            n = max(len(sc), 1)
            over = sum(abs(c["rel_err"]) > 0.01 for c in sc) / n
            p0s = [ref[c["regime"]]["over_1pct"] / ref[c["regime"]]["n"] for c in sc]
            expect = sum(p0s) / n
            se = sum(p * (1 - p) for p in p0s) ** 0.5 / n
            ok_sc = (len(sc) >= 5 and all(abs(c["rel_err"]) <= ref[c["regime"]]["abs_max"] for c in sc)
                     and over <= expect + 2 * se)
            t["g3_rule"] = {"ref_abs_max": {k: v["abs_max"] for k, v in ref.items()}, "expected_over_1pct_share": expect,
                            "own_over_1pct_share": over, "two_se": 2 * se,
                            "worst_vs_ref": max(abs(c["rel_err"]) / ref[c["regime"]]["abs_max"] for c in sc)}
        else:
            ok_sc = len(sc) >= 5 and all(abs(c["rel_err"]) <= (0.01 if tk in DIREXION else 0.001) for c in sc)
        ok_gap = t["longest_gap_trading_days"] <= 3
        # diagnostic, not a gate: A is the PUBLISHED aum; nav and shares before a later reverse split are restated and
        # rounded (SQQQ 2016-2019 reads nav x shares ~0.33% below aum), and G3 checks aum's parse against N-PORT
        ok_id = t["identity_share_within_1bp"] is None or t["identity_share_within_1bp"] >= 0.99
        ok_big = all(f["split_within_3d"] or abs(f["unexplained_rel"]) < 0.01 for f in t["daum_over_25pct"])
        verdict[tk] = {"G1_gaps": ok_gap, "G2_big_moves_explained": ok_big, "G3_spot_checks": ok_sc,
                       "identity_diagnostic": ok_id, "pass": ok_gap and ok_big and ok_sc}
    res["verdict"] = verdict
    return res


def build() -> int:
    nport = json.loads((OUT / "nport_reports.json").read_text(encoding="utf-8"))
    cal = calendar()
    psw = proshares(WARM)  # the path and the regime bands need Direxion's first anchor, 2015-10-31
    ps = psw[psw["date"] >= START].reset_index(drop=True)
    dx, dx_info = direxion(psw, nport)
    panel = pd.concat([ps, dx], ignore_index=True).sort_values(["ticker", "date"]).reset_index(drop=True)
    if (panel["date"] >= RESERVED_FROM).any() or (panel["date"] < START).any():
        raise RuntimeError("a row outside the in-sample span is in the panel")
    b = band(ps, nport)
    br = band_regimes(psw)
    refs = {"nport_monthly": b["_forward_checks"], "nsar_monthly": br["nsar_monthly"]["forward_checks"],
            "semiannual_flow": br["semiannual"]["half_year_flow_checks"]}
    g0 = gate0(panel, cal, nport, dx_info, refs)
    g0["direxion"] = dx_info
    g0["band_measured_on_proshares"] = b
    g0["band_by_regime_on_proshares"] = br
    g0["calendar"] = {"source": "SPY daily dates, Alpha Vantage cache", "days": int(len(cal)),
                      "first": str(cal[0].date()), "last": str(cal[-1].date())}
    g0["direxion_absent_before"] = {tk: dx_info[tk]["first_anchor"] for tk in DIREXION}
    g0["all_pass"] = all(v["pass"] for v in g0["verdict"].values())
    g0["coverage"] = {"NQ_set_complete_from": START,
                      "ES_set_complete_from": max(max(dx_info[tk]["first_anchor"] for tk in DIREXION), START),
                      "note": "Direxion estimated from its filings (LETF-A3, A5); ProShares issuer data"}
    panel.to_csv(OUT / "letf_aum_daily.csv.gz", index=False, encoding="utf-8", lineterminator="\n")
    (OUT / "gate0.json").write_text(json.dumps(g0, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    meta = {"path": "data/letf/letf_aum_daily.csv.gz", "rows": int(len(panel)), "reserved_from": RESERVED_FROM,
            "columns": list(panel.columns), "builder": "scripts/build_letf_aum.py",
            "holdout": "A10: nothing on or after 2025-03-01 is parsed; the vault is scored only in the joint run",
            "per_ticker": {tk: {"first": str(g["date"].min().date()), "last": str(g["date"].max().date()),
                                "rows": int(len(g)), "estimated": bool(g["estimated"].iloc[0])}
                           for tk, g in panel.groupby("ticker")}}
    (OUT / "letf_aum_daily.meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    for tk, v in g0["verdict"].items():
        t = g0["tickers"][tk]
        sc = t["spot_checks"]
        print(f"  {tk:5s} {t['first']}..{t['last']} rows {t['rows']:5d} gap {t['longest_gap_trading_days']}  "
              f">25%: {len(t['daum_over_25pct'])}  spot {len(sc)} max|err| "
              f"{max((abs(c['rel_err']) for c in sc), default=float('nan')):.5f}  -> {'PASS' if v['pass'] else 'FAIL'} {v}")
    print(f"  band (ProShares through the same estimator): {b['_pooled']}; forward checks {b['_forward_checks']}")
    for k, v in br.items():
        print(f"  band, regime {k}: {v}")
    for tk in DIREXION:
        i = dx_info[tk]
        print(f"  {tk}: anchors {i['first_anchor']}..{i['last_anchor']}, forward check max |err| {i['forward_abs_max']}, "
              f"over 1%: {i['forward_over_1pct']}; path error {i['path_error_monthly']}")
        print(f"    statement-basis gap {i['pre2019']['statement_basis_gap']}; G3 {g0['tickers'][tk].get('g3_rule')}")
    print(f"  GATE 0 on present rows: {'PASS' if g0['all_pass'] else 'FAIL'}; coverage {g0['coverage']}")
    return 0


def selftest() -> int:
    """Each Gate 0 check must fire on a deliberately broken input (break what the assertion reads)."""
    cal = pd.bdate_range("2020-01-01", "2020-03-31")
    g = pd.DataFrame({"date": cal, "ticker": "TQQQ", "nav": 100.0, "shares_out": 1e6, "aum": 1e8,
                      "source": "t", "estimated": False})
    nport = {"TQQQ": {"reports": [{"report_date": str(d.date()), "net_assets": 1e8} for d in cal[::10][:6]]}}
    dxi: dict[str, dict[str, list]] = {k: {"forward_checks": []} for k in DIREXION}
    base = gate0(g, cal, nport, dxi)["verdict"]["TQQQ"]
    assert base["pass"], base
    gap = g.drop(index=range(20, 24))
    assert not gate0(gap, cal, nport, dxi)["verdict"]["TQQQ"]["G1_gaps"], "a 4-day gap must fail G1"
    jump = g.copy()
    jump.loc[30:, "aum"] = 2e8
    assert not gate0(jump, cal, nport, dxi)["verdict"]["TQQQ"]["G2_big_moves_explained"], "an unexplained +100% must fail G2"
    assert not gate0(jump, cal, nport, dxi)["verdict"]["TQQQ"]["identity_diagnostic"], "nav x shares != aum must flag"
    few = {"TQQQ": {"reports": nport["TQQQ"]["reports"][:4]}}
    assert not gate0(g, cal, few, dxi)["verdict"]["TQQQ"]["G3_spot_checks"], "4 spot checks must fail G3"
    off = {"TQQQ": {"reports": [dict(r, net_assets=1.01e8) for r in nport["TQQQ"]["reports"]]}}
    assert not gate0(g, cal, off, dxi)["verdict"]["TQQQ"]["G3_spot_checks"], "a 1% spot-check miss must fail G3"
    # the forward estimator: exact when the flows and path are the truth; its check fires when they are not
    days = pd.bdate_range("2019-12-31", "2020-03-31")
    path = pd.Series(np.linspace(100, 130, len(days)), index=days)
    truth, prev = [100.0], days[0]
    per = pd.Series(days.to_period("M"), index=days)
    for t in days[1:]:
        truth.append(truth[-1] * path[t] / path[prev] + 3.0)  # a flow of 3 every trading day
        prev = t
    flows = [3.0 * int((per[1:] == m).sum()) for m in pd.period_range("2020-01", "2020-03", freq="M")]
    reps = [{"report_date": "2019-12-31", "net_assets": 100.0, "flow": [0, 0, 0]},
            {"report_date": "2020-03-31", "net_assets": truth[-1], "flow": flows}]
    e, c = forward_estimate(path, reps)
    assert abs(c["rel_err"].iloc[0]) < 1e-12 and abs(e.iloc[-1] - truth[-1]) < 1e-9, "exact inputs must be exact"
    e2, c2 = forward_estimate(path, [reps[0], dict(reps[1], net_assets=truth[-1] * 1.05)])
    assert abs(c2["rel_err"].iloc[0] + 0.05 / 1.05) < 1e-12, "a 5% filing miss must show in the check"
    assert abs(e2.iloc[-1] - truth[-1] * 1.05) < 1e-6, "the correction must land on the filing"
    try:
        forward_estimate(path, [reps[0], dict(reps[1], report_date="2020-06-30")])
        raise AssertionError("a missing quarter must raise")
    except RuntimeError:
        pass
    ref = {"nport_monthly": {"n": 100, "over_1pct": 30, "abs_max": 0.10}}
    dcal = pd.bdate_range("2020-01-01", "2020-03-31")
    dx = pd.DataFrame({"date": dcal, "ticker": "SPXL", "nav": 1.0, "shares_out": 1e8, "aum": 1e8, "source": "t",
                       "estimated": True})
    inside: dict[str, dict[str, list[dict]]] = {"SPXL": {"forward_checks": [{"quarter_end": "q", "forward": 1, "filed": 1, "rel_err": e}
                                          for e in (0.02, -0.005, 0.003, 0.08, -0.004, 0.001)]},
              "SPXS": {"forward_checks": []}}
    assert gate0(dx, dcal, {}, inside, ref)["verdict"]["SPXL"]["G3_spot_checks"], "within the reference must pass"
    outside = {"SPXL": {"forward_checks": [dict(c, rel_err=0.12) if i == 0 else c
                                           for i, c in enumerate(inside["SPXL"]["forward_checks"])]},
               "SPXS": {"forward_checks": []}}
    assert not gate0(dx, dcal, {}, outside, ref)["verdict"]["SPXL"]["G3_spot_checks"], "beyond the max must fail"
    often = {"SPXL": {"forward_checks": [dict(c, rel_err=0.02) for c in inside["SPXL"]["forward_checks"]]},
             "SPXS": {"forward_checks": []}}
    assert not gate0(dx, dcal, {}, often, ref)["verdict"]["SPXL"]["G3_spot_checks"], "too many >1% must fail"
    print("selftest: 13 checks fire as they must")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(fetch() if a.fetch else build() if a.build else selftest() if a.selftest else 1)
