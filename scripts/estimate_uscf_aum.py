"""Daily shares and AUM for UNG and USO, estimated between their audited month-ends (AITODO 1e).

SPEC -- written 2026-09-24 before any estimate was compared with anything, and frozen from then on.

WHY. UNG's and USO's roll flows (Stage F) are sized by the contracts each fund holds, which is AUM x
f_fut / (price x multiplier). No free daily NAV or share series exists for either fund. What does
exist is each month-end's shares and NAV per share, from their Rule 4.22 monthly statements
(`data/fund_facts/uscf_monthly_statements.csv`, gated against the audited quarter-ends), and each
trading day's market close (the Alpha Vantage cache, cut to dates before 2024-01-01).

THE ESTIMATE, per fund and NYSE day d, 2017-05-22 → 2023-12-29:
  * shares_est: linear in trading days between the two bounding month-end share counts. A month
    missing from the statements is bridged across; its days are flagged `gap`. Where a reverse
    split falls inside a pair of month-ends, the earlier count is put on the later basis first.
    The known splits are USO 1-for-8 (month 2020-04) and UNG 1-for-4 (months 2017-12 and 2023-12,
    as restated in those statements).
  * nav_est: the market close scaled by the previous month-end's ratio (statement NAV per share /
    that day's close), which corrects the level for the ETF's premium.
  * aum_est = shares_est x nav_est.
  * shares_pit: the share count of the latest statement whose FILING date (the date in the file
    name) is on or before d. It is written beside the estimate. The estimate itself uses the next
    month-end, which is hindsight, and the interpolation cannot see creations inside the month.

THE ERROR BAND, measured where the truth exists: the identical method (month-end anchors from the
truth, linear in trading days) is run on BOIL, KOLD, UCO and SCO, whose daily shares are in
`fund_nav_daily`. The band is the p10 and p90 of the relative share error, pooled over those
funds on 2017-05-22 → 2023-12-29. Published AUM is used, not NAV x shares, because of BOIL's
rounding (1a). Reported: median |error|, p90 |error|, and the same for a quarter-end-anchored
version, so the gain from monthly anchors is measured.

WHAT THIS DOES NOT TOUCH: all reads are before 2024-01-01. It computes no strategy return and no
flow statistic. It writes `data/ledger_uscf_aum_daily.csv.gz` (gitignored by suffix) and
`data/ledger_uscf_aum_summary.json`.

    uv run python scripts/estimate_uscf_aum.py            # write both
    uv run python scripts/estimate_uscf_aum.py --check    # rebuild, compare byte for byte
"""
from __future__ import annotations

import argparse
import bisect
import gzip
import importlib.util
import io
import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
STMT = REPO / "data" / "fund_facts" / "uscf_monthly_statements.csv"
AV = REPO / "data" / "raw" / "alphavantage" / "daily_adjusted_etf"
OUT_ROWS = REPO / "data" / "ledger_uscf_aum_daily.csv.gz"
OUT_SUM = REPO / "data" / "ledger_uscf_aum_summary.json"
RESERVED_FROM = "2024-01-01"
FIRST, LAST = "2017-05-22", "2023-12-29"
#: (fund, month of the restated statement) -> reverse-split factor k: shares before / k = shares after
SPLITS = {("USO", "2020-04"): 8, ("UNG", "2017-12"): 4, ("UNG", "2023-12"): 4}
PROSHARES = ("BOIL", "KOLD", "UCO", "SCO")
#: split effective days beyond the 2024 cut, from the fund's filing (UNG 10-Q 2024-Q1: "On January 23, 2024")
AFTER_CUT = {("UNG", "2023-12"): "2024-01-23"}


class AumError(RuntimeError):
    pass


def _gate0b() -> Any:
    spec = importlib.util.spec_from_file_location("gate_0b_ng_nav", REPO / "scripts" / "gate_0b_ng_nav.py")
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules["gate_0b_ng_nav"] = m
    spec.loader.exec_module(m)
    return m


G = _gate0b()


def closes(fund: str) -> pd.Series:
    with gzip.open(AV / f"{fund}.json.gz", "rt", encoding="utf-8") as fh:
        raw = json.load(fh)
    s = pd.Series({d: float(v["4. close"]) for d, v in raw.items() if d < RESERVED_FROM}).sort_index()
    if (s.index >= RESERVED_FROM).any():
        raise AumError("a close on or after the seal is in memory")
    return s


def interpolate(days: list[str], anchors: list[tuple[str, float]]) -> tuple[np.ndarray, np.ndarray]:
    """Linear in trading-day index between anchor dates (each anchor at the last day <= its date)."""
    idx = np.array([bisect.bisect_right(days, a) - 1 for a, _ in anchors])
    vals = np.array([v for _, v in anchors], dtype=float)
    keep = idx >= 0
    idx, vals = idx[keep], vals[keep]
    x = np.arange(len(days))
    return np.interp(x, idx, vals), idx


def validate_on_proshares() -> dict[str, Any]:
    nav = G.load_panel("fund_nav_daily", reserved_from=RESERVED_FROM, usecols=["date", "fund", "shares_out", "aum"]).frame
    out: dict[str, Any] = {}
    pooled_m, pooled_q = [], []
    for fund in PROSHARES:
        g = nav[nav["fund"] == fund].sort_values("date")
        g = g[(g["date"] >= "2017-04-01") & (g["date"] <= LAST)]
        days = list(g["date"].astype(str))
        truth = g["aum"].astype(float).to_numpy() / 1.0
        # month-end and quarter-end anchors on AUM-implied shares would mix NAV moves; anchor the SHARE count
        sh = g["shares_out"].astype(float).to_numpy()
        me = g.groupby(g["date"].astype(str).str[:7])["date"].max().astype(str).tolist()
        qe = [d for d in me if d[5:7] in ("03", "06", "09", "12")]
        pos = {d: i for i, d in enumerate(days)}
        est_m, _ = interpolate(days, [(d, sh[pos[d]]) for d in me])
        est_q, _ = interpolate(days, [(d, sh[pos[d]]) for d in qe])
        win = np.array([FIRST <= d <= LAST for d in days])
        ok = win & (sh > 0)
        em = (est_m[ok] - sh[ok]) / sh[ok]
        eq = (est_q[ok] - sh[ok]) / sh[ok]
        pooled_m.append(em)
        pooled_q.append(eq)
        out[fund] = {"days": int(ok.sum()),
                     "monthly_anchor": {"median_abs": round(float(np.median(np.abs(em))), 5), "p90_abs": round(float(np.quantile(np.abs(em), 0.9)), 5)},
                     "quarterly_anchor": {"median_abs": round(float(np.median(np.abs(eq))), 5), "p90_abs": round(float(np.quantile(np.abs(eq), 0.9)), 5)}}
        _ = truth
    pm, pq = np.concatenate(pooled_m), np.concatenate(pooled_q)
    out["pooled"] = {"monthly_anchor": {"median_abs": round(float(np.median(np.abs(pm))), 5), "p90_abs": round(float(np.quantile(np.abs(pm), 0.9)), 5),
                                        "p10": round(float(np.quantile(pm, 0.1)), 5), "p90": round(float(np.quantile(pm, 0.9)), 5)},
                     "quarterly_anchor": {"median_abs": round(float(np.median(np.abs(pq))), 5), "p90_abs": round(float(np.quantile(np.abs(pq), 0.9)), 5)}}
    return out


def build() -> tuple[str, dict[str, Any]]:
    val = validate_on_proshares()
    lo_rel, hi_rel = val["pooled"]["monthly_anchor"]["p10"], val["pooled"]["monthly_anchor"]["p90"]
    st = pd.read_csv(STMT, encoding="utf-8", dtype={"fund": str, "month_end": str, "source": str})
    lines = ["fund,date,shares_est,shares_lo,shares_hi,nav_est,aum_est,aum_lo,aum_hi,shares_pit,flag"]
    summary: dict[str, Any] = {"validation_on_proshares": val, "band_rel": [lo_rel, hi_rel], "funds": {}}
    for fund in ("UNG", "USO"):
        s = st[st["fund"] == fund].sort_values("month_end").reset_index(drop=True)
        # put every earlier count on the basis of the latest split in the window
        factor = np.ones(len(s))
        for (f, month), k in SPLITS.items():
            if f == fund:
                factor[s["month_end"].str[:7] < month] *= k
        s["shares_adj"] = s["shares"] / factor
        s["nps_adj"] = s["nav_per_share"] * factor
        px = closes(fund)
        days = [d for d in px.index if "2017-01-01" <= d <= LAST]
        # the AV close is split-ADJUSTED? no: '4. close' is raw; put it on the same basis
        cfactor = np.ones(len(days))
        split_days: dict[str, str] = {}
        for (f, month), k in SPLITS.items():
            if f != fund:
                continue
            if (f, month) in AFTER_CUT:
                eff = AFTER_CUT[(f, month)]  # beyond the cut, so taken from the filing, not detected
            else:
                # the raw close changes basis on the effective day: the ONE day in the neighbourhood
                # whose close / previous close is within [0.75k, 1.33k]
                lo_d = (pd.Timestamp(month + "-01") - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
                hi_d = (pd.Timestamp(month + "-01") + pd.Timedelta(days=75)).strftime("%Y-%m-%d")
                cand = [days[i] for i in range(1, len(days)) if lo_d <= days[i] <= hi_d
                        and 0.75 * k <= px[days[i]] / px[days[i - 1]] <= 1.33 * k]
                if len(cand) != 1:
                    raise AumError(f"{fund} split {month} (1-for-{k}): {len(cand)} candidate effective days {cand}")
                eff = cand[0]
            split_days[f"{month} 1-for-{k}"] = eff
            cfactor[np.array(days) < eff] *= k
        close_adj = px.loc[days].to_numpy() * cfactor
        est, aidx = interpolate(days, list(zip(s["month_end"], s["shares_adj"])))
        # premium correction from the previous month-end anchor
        me_pos = {d: bisect.bisect_right(days, d) - 1 for d in s["month_end"]}
        ratio = np.full(len(days), np.nan)
        for d, nps in zip(s["month_end"], s["nps_adj"]):
            i = me_pos[d]
            if i >= 0:
                ratio[i:] = nps / close_adj[i]
        nav_est = close_adj * ratio
        gaps = set()
        months = s["month_end"].str[:7].tolist()
        for a, b in zip(months, months[1:]):
            ya, ma = int(a[:4]), int(a[5:7])
            if int(b[:4]) * 12 + int(b[5:7]) - (ya * 12 + ma) > 1:
                gaps.add((a, b))
        # filing date = the date in the file name (plain '8-k' names and derived rows included)
        filed = sorted((re.search(r"(\d{8})(?:pdf)?\.pdf$", str(src)).group(1), sh)  # type: ignore[union-attr]
                       for src, sh in zip(s["source"], s["shares_adj"]))
        fdates = [f"{x[:4]}-{x[4:6]}-{x[6:]}" for x, _ in filed]
        rows_out = 0
        for i, d in enumerate(days):
            if not (FIRST <= d <= LAST) or np.isnan(nav_est[i]):
                continue
            j = bisect.bisect_right(fdates, d) - 1
            pit = filed[j][1] if j >= 0 else float("nan")
            flag = "gap" if any(a < d[:7] < b for a, b in gaps) else ""
            sh = est[i]
            lines.append(f"{fund},{d},{sh!r},{sh * (1 + lo_rel)!r},{sh * (1 + hi_rel)!r},{nav_est[i]!r},"
                         f"{sh * nav_est[i]!r},{sh * (1 + lo_rel) * nav_est[i]!r},{sh * (1 + hi_rel) * nav_est[i]!r},{pit!r},{flag}")
            rows_out += 1
        # self-check: at every month-end in the window the estimate equals the statement exactly
        mism = [d for d, v in zip(s["month_end"], s["shares_adj"]) if FIRST <= d <= LAST
                and me_pos[d] >= 0 and days[me_pos[d]][:7] == d[:7] and abs(est[me_pos[d]] - v) > 1e-6]
        if mism:
            raise AumError(f"{fund}: interpolation misses its own anchors at {mism[:3]}")
        summary["funds"][fund] = {"rows": rows_out, "anchors": len(s), "gap_months": sorted(f"{a}..{b}" for a, b in gaps),
                                  "split_effective_days": split_days}
        _ = aidx
    return "\n".join(lines) + "\n", summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    text, summary = build()
    stext = json.dumps(summary, indent=1, sort_keys=True) + "\n"
    if a.check:
        with gzip.open(OUT_ROWS, "rt", encoding="utf-8", newline="") as fh:
            if fh.read() != text:
                raise AumError(f"{OUT_ROWS.name} does not reproduce")
        if OUT_SUM.read_text(encoding="utf-8") != stext:
            raise AumError(f"{OUT_SUM.name} does not reproduce")
        print("[check] both outputs reproduce byte for byte")
        return 0
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(text.encode("utf-8"))
    OUT_ROWS.write_bytes(buf.getvalue())
    OUT_SUM.write_text(stext, encoding="utf-8", newline="\n")
    v = summary["validation_on_proshares"]
    for f in (*PROSHARES, "pooled"):
        print(f"{f:6s} monthly anchors {v[f]['monthly_anchor']}  quarterly {v[f]['quarterly_anchor']}")
    print(f"band (rel, p10..p90): {summary['band_rel']}")
    for f, s in summary["funds"].items():
        print(f"{f}: {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
