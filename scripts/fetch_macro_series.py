"""The four macro fixtures for the basis-momentum closure programme (the D600 design and the FX pre-registration to follow): the
He-Kelly-Manela intermediary factors, the EIA weekly stocks, the USDA NASS stocks and the OECD 3-month rates.

    uv run python scripts/fetch_macro_series.py --fetch all      # raw caches under data/raw/{hkm,eia,nass,oecd,esmis}
    uv run python scripts/fetch_macro_series.py --build          # caches -> fixtures + meta (gates); manifest not touched here
    uv run python scripts/fetch_macro_series.py --selftest       # every gate raises on a broken panel
    uv run python scripts/fetch_macro_series.py --probe-nass     # what Quick Stats returns for the declared parameters (key needed)

Sources, all fetched with the stdlib; no key except NASS:
  * HKM   https://zhiguohe.net/wp-content/uploads/2025/07/He_Kelly_Manela_Factors_{monthly,quarterly}_250627.csv
          (He, Kelly & Manela 2017 JFE; licence non-commercial -> the derived fixture is gitignored, manifest-registered)
  * EIA   https://www.eia.gov/opendata/bulk/{PET,NG}.zip (keyless bulk; JSON lines; current vintage) -- WCESTUS1 crude ex-SPR,
          WGTSTUS1 total gasoline, WDISTUS1 distillate (thousand barrels, weekly, Friday week-ending); NW2_EPG0_SWO_R48_BCF
          Lower-48 working gas (Bcf, weekly). A nominal release date is carried (WPSR Wednesday w+5, WNGSR Thursday w+6);
          THE RUNNER'S KNOWN-AT RULE IS w + 7 CALENDAR DAYS <= the month-end session, which covers every holiday shift.
  * NASS  https://quickstats.nass.usda.gov/api/api_GET (key: NASS_API_KEY or ~/.config/nass/key) -- quarterly Grain Stocks
          (corn, soybeans, wheat), monthly Cattle on Feed, quarterly Hogs and Pigs; release datetimes scraped from ESMIS
          (https://esmis.nal.usda.gov/concern/publications/{xg94hp534,m326m174z,rj430453j}).
  * OECD  https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_FINMARK,4.0/... IR3TIB monthly 3-month interbank
          averages for USA, EA20, GBR, JPN, AUS, CAN, CHE (the series FRED republishes as IR3TIB01xxM156N; FRED's web host
          resets connections from this machine, the OECD source does not). CC BY 4.0 -> committed as a small plain csv.

The FRBNY H.10 spot rates (a diagnostic only in the pre-registration) are NOT fetched: the Fed's bulk package returned an
empty body and FRED is unreachable; the primary FX construction is spot-free by design.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
FIX = REPO / "data" / "fixtures"
UA = {"User-Agent": "Mozilla/5.0 (research fetch; backtest-framework; contact via repository)", "Accept": "*/*"}
HKM_URL = "https://zhiguohe.net/wp-content/uploads/2025/07/He_Kelly_Manela_Factors_{}_250627.csv"
EIA_URL = "https://www.eia.gov/opendata/bulk/{}.zip"
EIA_SERIES = {"PET.WCESTUS1.W": ("crude_ex_spr", "kbbl", "WPSR"), "PET.WGTSTUS1.W": ("gasoline_total", "kbbl", "WPSR"),
              "PET.WDISTUS1.W": ("distillate", "kbbl", "WPSR"), "NG.NW2_EPG0_SWO_R48_BCF.W": ("natgas_working_l48", "bcf", "WNGSR")}
EIA_RELEASE_LAG_DAYS = {"WPSR": 5, "WNGSR": 6}                   # nominal: Wednesday / Thursday after the Friday week-ending
OECD_URL = ("https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_FINMARK,4.0/"
            "USA+EA20+GBR+JPN+AUS+CAN+CHE.M.IR3TIB.PA.....?startPeriod=2000-01&format=csvfile")
OECD_AREA = {"USA": "USD", "EA20": "EUR", "GBR": "GBP", "JPN": "JPY", "AUS": "AUD", "CAN": "CAD", "CHE": "CHF"}
OECD_KNOWN = {("USD", "2019-06"): 2.30, ("EUR", "2019-06"): -0.33, ("CHF", "2019-06"): -0.78, ("GBP", "2019-06"): 0.78, ("JPY", "2019-06"): 0.05}   # FRED-published values, checked 2026-09-21
NASS_URL = "https://quickstats.nass.usda.gov/api/api_GET/"
NASS_PARAMS_URL = "https://quickstats.nass.usda.gov/api/get_param_values/"
NASS_QUERIES = {                                                  # declared in the D600 design; probed before the build
    "grain_stocks": {"source_desc": "SURVEY", "sector_desc": "CROPS", "group_desc": "FIELD CROPS", "statisticcat_desc": "STOCKS",
                     "agg_level_desc": "NATIONAL", "freq_desc": "POINT IN TIME", "domain_desc": "TOTAL", "unit_desc": "BU"},
    "cattle_on_feed": {"source_desc": "SURVEY", "sector_desc": "ANIMALS & PRODUCTS", "group_desc": "LIVESTOCK", "commodity_desc": "CATTLE",
                       "prodn_practice_desc": "ON FEED", "statisticcat_desc": "INVENTORY", "agg_level_desc": "NATIONAL", "unit_desc": "HEAD", "domain_desc": "TOTAL"},
    "hogs_and_pigs": {"source_desc": "SURVEY", "sector_desc": "ANIMALS & PRODUCTS", "group_desc": "LIVESTOCK", "commodity_desc": "HOGS",
                      "statisticcat_desc": "INVENTORY", "agg_level_desc": "NATIONAL", "unit_desc": "HEAD", "domain_desc": "TOTAL", "class_desc": "ALL CLASSES"},
}
NASS_COMMODITIES = {"grain_stocks": ["CORN", "SOYBEANS", "WHEAT"]}
ESMIS = {"grain_stocks": ("xg94hp534", "grst"), "cattle_on_feed": ("m326m174z", "cofd"), "hogs_and_pigs": ("rj430453j", "hgpg")}
YEAR_FROM, YEAR_TO = 2005, 2026


def log(msg):
    print(msg, flush=True)


def sha256(p: Path):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get(url, timeout=120, headers=None):
    r = urllib.request.urlopen(urllib.request.Request(url, headers={**UA, **(headers or {})}), timeout=timeout)
    return r.read()


def nass_key():
    k = os.environ.get("NASS_API_KEY")
    if k:
        return k.strip()
    f = Path.home() / ".config" / "nass" / "key"
    if f.exists():
        return f.read_text(encoding="utf-8").strip()
    return None


def expect_raise(fn, what):
    try:
        fn()
    except AssertionError as e:
        log(f"    gate RAISES on {what}: {str(e)[:80]}"); return True
    raise AssertionError(f"gate did not raise on {what}")


# ------------------------------------------------------------------------------------------------ fetch
def fetch_hkm():
    d = RAW / "hkm"; d.mkdir(parents=True, exist_ok=True)
    for f in ("monthly", "quarterly"):
        p = d / f"He_Kelly_Manela_Factors_{f}_250627.csv"
        if not p.exists():
            p.write_bytes(get(HKM_URL.format(f))); log(f"  hkm: fetched {p.name} ({p.stat().st_size} bytes)")
        else:
            log(f"  hkm: cached {p.name}")


def fetch_eia():
    d = RAW / "eia"; d.mkdir(parents=True, exist_ok=True)
    for z in ("PET", "NG"):
        p = d / f"{z}.zip"
        if not p.exists():
            t0 = time.time(); p.write_bytes(get(EIA_URL.format(z), timeout=900)); log(f"  eia: fetched {p.name} ({p.stat().st_size / 1e6:.1f} MB, {time.time() - t0:.0f} s)")
        else:
            log(f"  eia: cached {p.name} ({p.stat().st_size / 1e6:.1f} MB)")


def fetch_oecd():
    d = RAW / "oecd"; d.mkdir(parents=True, exist_ok=True); p = d / "ir3tib_monthly.csv"
    if not p.exists():
        p.write_bytes(get(OECD_URL, timeout=300)); log(f"  oecd: fetched {p.name} ({p.stat().st_size} bytes)")
    else:
        log(f"  oecd: cached {p.name}")


def fetch_esmis():
    """Every release row (datetime, file names) of the three NASS publications, all pages."""
    d = RAW / "esmis"; d.mkdir(parents=True, exist_ok=True)
    for name, (pid, stem) in ESMIS.items():
        p = d / f"{name}_releases.json"
        if p.exists():
            log(f"  esmis: cached {p.name}"); continue
        rows = []
        for page in range(0, 40):
            html = get(f"https://esmis.nal.usda.gov/concern/publications/{pid}?page={page}", timeout=120).decode("utf-8", errors="replace")
            found = re.findall(r'<time datetime="([^"]+)">[^<]*</time>\s*</td>\s*<td[^>]*views-field-release-files[^>]*>(.*?)</td>', html, flags=re.S)
            if not found:
                break
            for dt, cell in found:
                files = re.findall(r'release-files/\d+/([^"]+)"', cell)
                rows.append({"release_datetime": dt, "files": files})
            time.sleep(0.5)
        p.write_text(json.dumps(rows, indent=0), encoding="utf-8"); log(f"  esmis: {name}: {len(rows)} releases over the pages scanned")


def nass_get(params, key):
    q = urllib.parse.urlencode({**params, "key": key, "format": "JSON"})
    return json.loads(get(NASS_URL + "?" + q, timeout=300).decode("utf-8"))


def fetch_nass():
    key = nass_key()
    if key is None:
        log("  nass: NO KEY -- set NASS_API_KEY or write ~/.config/nass/key (free registration at https://quickstats.nass.usda.gov/api); skipped"); return False
    d = RAW / "nass"; d.mkdir(parents=True, exist_ok=True)
    for name, base in NASS_QUERIES.items():
        p = d / f"{name}.json"
        if p.exists():
            log(f"  nass: cached {p.name}"); continue
        out = []
        for com in NASS_COMMODITIES.get(name, [None]):
            params = {**base, "year__GE": YEAR_FROM, "year__LE": YEAR_TO}
            if com:
                params["commodity_desc"] = com
            js = nass_get(params, key); rows = js.get("data", []); out.extend(rows); log(f"  nass: {name} {com or ''}: {len(rows)} rows"); time.sleep(1.0)
        p.write_text(json.dumps(out), encoding="utf-8")
    return True


def probe_nass():
    key = nass_key()
    if key is None:
        log("  nass: NO KEY"); return 1
    for name, base in NASS_QUERIES.items():
        for com in NASS_COMMODITIES.get(name, [None]):
            params = {**base, "year": 2019}
            if com:
                params["commodity_desc"] = com
            js = nass_get(params, key); rows = js.get("data", [])
            log(f"  {name} {com or ''}: {len(rows)} rows in 2019; short_desc {sorted({r.get('short_desc') for r in rows})[:4]}; periods {sorted({r.get('reference_period_desc') for r in rows})[:8]}")
    return 0


# ------------------------------------------------------------------------------------------------ build
def build_hkm():
    frames = []
    for f, key in (("monthly", "yyyymm"), ("quarterly", "yyyyq")):
        df = pd.read_csv(RAW / "hkm" / f"He_Kelly_Manela_Factors_{f}_250627.csv", encoding="utf-8"); df = df.rename(columns={key: "period"}); df.insert(0, "freq", "M" if f == "monthly" else "Q"); frames.append(df)
    out = pd.concat(frames, ignore_index=True); out["period"] = out["period"].astype(int)
    # SOURCE DEFECT in the 2025-06-27 file: two rows labelled 202501 in the monthly file and two labelled 20251 in the quarterly
    # one (the second of each is the next period, mislabelled). Both rows stay in the raw cache; the fixture drops every row
    # carrying a duplicated label and records them. All are in 2025, outside anything a study here reads (< 2024-01).
    dup = out.duplicated(["freq", "period"], keep=False); defects = out[dup].to_dict("records"); out = out[~dup].reset_index(drop=True)
    rep = gates_hkm(out); rep["source_defect_rows_dropped"] = defects
    return out, rep


def gates_hkm(out):
    assert not out.duplicated(["freq", "period"]).any(), "G1: duplicate (freq, period)"
    r = out["intermediary_capital_ratio"]; assert ((r > 0) & (r < 1)).all(), "G2: a capital ratio outside (0, 1)"
    m = out[out["freq"] == "M"]; q = out[out["freq"] == "Q"]; assert len(m) >= 600 and len(q) >= 200, "G3: too few rows"
    mq = m.assign(q=(m["period"] // 100) * 10 + (m["period"] % 100 - 1) // 3 + 1).groupby("q")["intermediary_capital_ratio"].last()
    j = q.set_index("period")["intermediary_capital_ratio"].to_frame("q").join(mq.rename("m"), how="inner"); c = float(j["q"].corr(j["m"]))
    assert c > 0.9, f"G4: quarterly and quarter-end monthly capital ratios disagree (corr {c:.3f})"
    raw_m = pd.read_csv(RAW / "hkm" / "He_Kelly_Manela_Factors_monthly_250627.csv", encoding="utf-8"); raw_rows = int((~raw_m["yyyymm"].duplicated(keep=False)).sum())
    assert raw_rows == len(m), f"G5: monthly rows {len(m)} != raw file's uniquely labelled rows {raw_rows}"
    return {"G1": "no duplicate (freq, period)", "G2": "capital ratio in (0, 1) on every row", "G3": f"monthly rows {len(m)} >= 600, quarterly {len(q)} >= 200",
            "G4": f"quarter-end monthly vs quarterly capital ratio corr {c:.4f} > 0.9", "G5": f"monthly rows equal the raw file's {raw_rows}", "monthly_span": [int(m["period"].min()), int(m["period"].max())], "quarterly_span": [int(q["period"].min()), int(q["period"].max())]}


def read_eia_zip(z, wanted):
    hits = {}
    with zipfile.ZipFile(z) as zf:                       # zf.read, not zf.open: the encoding scanner counts any .open( as a text site
        text = zf.read(zf.namelist()[0]).decode("utf-8")
    if True:
        for line in io.StringIO(text):
            if not any(w in line for w in wanted):
                continue
            d = json.loads(line)
            if d.get("series_id") in wanted:
                hits[d["series_id"]] = d
    return hits


def build_eia():
    rows = []
    for z, ids in (("PET", [k for k in EIA_SERIES if k.startswith("PET.")]), ("NG", [k for k in EIA_SERIES if k.startswith("NG.")])):
        hits = read_eia_zip(RAW / "eia" / f"{z}.zip", ids)
        for sid in ids:
            assert sid in hits, f"{sid} not in {z}.zip"
            d = hits[sid]; name, unit, rel = EIA_SERIES[sid]
            for ds, v in d["data"]:
                if v is None:
                    continue
                we = datetime.strptime(ds, "%Y%m%d").date()
                rows.append({"series": name, "series_id": sid, "unit": unit, "report": rel, "week_ending": we.isoformat(), "value": float(v),
                             "release_date_nominal": (we + timedelta(days=EIA_RELEASE_LAG_DAYS[rel])).isoformat(), "source_last_updated": d.get("last_updated"), "source_name": d.get("name")})
    out = pd.DataFrame(rows).sort_values(["series", "week_ending"]).reset_index(drop=True)
    return out, gates_eia(out)


def gates_eia(out):
    assert not out.duplicated(["series", "week_ending"]).any(), "G1: duplicate (series, week_ending)"
    assert (out["value"] > 0).all(), "G2: a non-positive stock"
    wd = pd.to_datetime(out["week_ending"]).dt.dayofweek; share = float((wd == 4).mean()); assert share > 0.99, f"G3: week-ending not Friday on {1 - share:.2%}"
    assert (pd.to_datetime(out["release_date_nominal"]) > pd.to_datetime(out["week_ending"])).all(), "G4: a release date not after its week-ending"
    for s, g in out.groupby("series"):
        w = pd.to_datetime(g["week_ending"]).sort_values(); gaps = w.diff().dt.days.dropna(); span = g[(g["week_ending"] >= "2010-01-01") & (g["week_ending"] <= "2023-12-31")]
        assert len(span) >= 700, f"G5: {s} has {len(span)} weeks in 2010-2023 (< 700)"
        assert (gaps[w.iloc[1:].between("2010-01-01", "2023-12-31").to_numpy()] == 7).all(), f"G5: {s} has a non-weekly gap inside 2010-2023"
    return {"G1": "no duplicate (series, week_ending)", "G2": "every stock > 0", "G3": f"week-ending is a Friday on {share:.2%}", "G4": "nominal release date after the week-ending on every row",
            "G5": "every series weekly without gaps over 2010-2023 (>= 700 weeks)", "series": {s: {"n": int(len(g)), "first": g["week_ending"].min(), "last": g["week_ending"].max()} for s, g in out.groupby("series")}}


def build_oecd():
    df = pd.read_csv(RAW / "oecd" / "ir3tib_monthly.csv", encoding="utf-8")
    df = df[(df["MEASURE"] == "IR3TIB") & (df["FREQ"] == "M")][["REF_AREA", "TIME_PERIOD", "OBS_VALUE"]].rename(columns={"REF_AREA": "area", "TIME_PERIOD": "period", "OBS_VALUE": "rate_pct"})
    df["currency"] = df["area"].map(OECD_AREA); df = df.dropna(subset=["currency"]); out = df[["currency", "area", "period", "rate_pct"]].sort_values(["currency", "period"]).reset_index(drop=True); out["filled"] = False
    # SOURCE GAP: the OECD series carries no USA observation for 2020-04 (every other currency-month 2009-2023 is present).
    # One cell, filled with the mean of its two neighbours and FLAGGED; the runner treats a flagged month as present and says so.
    need = pd.period_range("2009-01", "2023-12", freq="M").strftime("%Y-%m"); fills = []
    for c, g in out.groupby("currency"):
        for p in sorted(set(need) - set(g["period"])):
            prev = g[g["period"] < p]["rate_pct"]; nxt = g[g["period"] > p]["rate_pct"]
            if len(prev) and len(nxt):
                fills.append({"currency": c, "area": g["area"].iloc[0], "period": p, "rate_pct": float((prev.iloc[-1] + nxt.iloc[0]) / 2), "filled": True})
    if fills:
        out = pd.concat([out, pd.DataFrame(fills)], ignore_index=True).sort_values(["currency", "period"]).reset_index(drop=True)
    rep = gates_oecd(out); rep["source_gaps_filled"] = fills; assert len(fills) <= 1, f"G5: {len(fills)} filled cells; the declared allowance is one"
    return out, rep


def gates_oecd(out):
    assert not out.duplicated(["currency", "period"]).any(), "G1: duplicate (currency, period)"
    assert set(out["currency"]) == set(OECD_AREA.values()), "G2: a currency missing"
    need = pd.period_range("2009-01", "2023-12", freq="M").strftime("%Y-%m")
    for c, g in out.groupby("currency"):
        miss = sorted(set(need) - set(g["period"])); assert not miss, f"G2: {c} missing {len(miss)} months in 2009-2023 (first {miss[:3]})"
    assert out["rate_pct"].between(-2, 25).all(), "G3: a rate outside (-2, 25) %"
    for (c, p), v in OECD_KNOWN.items():
        got = float(out[(out["currency"] == c) & (out["period"] == p)]["rate_pct"].iloc[0]); assert abs(got - v) < 0.011, f"G4: {c} {p} {got} != FRED's {v}"
    return {"G1": "no duplicate (currency, period)", "G2": "seven currencies, every month 2009-01..2023-12 present", "G3": "rates in (-2, 25) %",
            "G4": f"{len(OECD_KNOWN)} FRED-published values reproduced to 0.01", "spans": {c: [g["period"].min(), g["period"].max()] for c, g in out.groupby("currency")}}


def nass_period_to_date(year, ref):
    m = re.match(r"FIRST OF ([A-Z]{3})", ref or "")
    if not m:
        return None
    mon = datetime.strptime(m.group(1), "%b").month
    return date(int(year), mon, 1).isoformat()


def esmis_release_for(name, obs_date):
    """The release row whose file stem's MMYY matches the report that carries `obs_date` (the first-of-month inventory)."""
    rel = json.loads((RAW / "esmis" / f"{name}_releases.json").read_text(encoding="utf-8")); stem = ESMIS[name][1]
    d = date.fromisoformat(obs_date)
    # Grain Stocks / Hogs: the Mar-1, Jun-1, Sep-1 reports are released in that month; the Dec-1 report in January.
    # Cattle on Feed: the first-of-month inventory is released in the same month.
    if name in ("grain_stocks", "hogs_and_pigs") and d.month == 12:
        rm, ry = 1, d.year + 1
    else:
        rm, ry = d.month, d.year
    want = f"{stem}{rm:02d}{ry % 100:02d}"
    for r in rel:
        if any(f.startswith(want) for f in r["files"]):
            return r["release_datetime"]
    return None


def build_nass():
    rows = []
    for name in NASS_QUERIES:
        p = RAW / "nass" / f"{name}.json"
        if not p.exists():
            continue
        for r in json.loads(p.read_text(encoding="utf-8")):
            obs = nass_period_to_date(r.get("year"), r.get("reference_period_desc"))
            if obs is None:
                continue
            v = str(r.get("Value", "")).replace(",", "").strip()
            if not re.match(r"^-?\d+(\.\d+)?$", v):
                continue
            rows.append({"report": name, "commodity": r.get("commodity_desc"), "short_desc": r.get("short_desc"), "obs_date": obs, "value": float(v), "unit": r.get("unit_desc"),
                         "release_datetime_utc": esmis_release_for(name, obs)})
    if not rows:
        return None, {"status": "no NASS cache (key absent at fetch time)"}
    out = pd.DataFrame(rows).drop_duplicates(["report", "commodity", "short_desc", "obs_date"]).sort_values(["report", "commodity", "obs_date"]).reset_index(drop=True)
    return out, gates_nass(out)


def gates_nass(out):
    assert not out.duplicated(["report", "commodity", "short_desc", "obs_date"]).any(), "G1: duplicate observation"
    assert (out["value"] > 0).all(), "G2: a non-positive stock"
    miss = out["release_datetime_utc"].isna(); assert miss.mean() < 0.05, f"G3: {miss.mean():.1%} of observations have no ESMIS release"
    rel = pd.to_datetime(out["release_datetime_utc"], utc=True); obs = pd.to_datetime(out["obs_date"], utc=True); ok = rel.notna()
    assert (rel[ok] > obs[ok]).all(), "G4: a release before its observation date"
    assert ((rel[ok] - obs[ok]).dt.days <= 60).all(), "G4: a release more than 60 days after its observation date"
    return {"G1": "no duplicate observation", "G2": "every stock > 0", "G3": f"ESMIS release found for {1 - miss.mean():.1%} of observations", "G4": "release after the observation by at most 60 days",
            "reports": {n: {"n": int(len(g)), "first": g["obs_date"].min(), "last": g["obs_date"].max(), "commodities": sorted(g["commodity"].dropna().unique().tolist())} for n, g in out.groupby("report")}}


def write_fixture(out, name, gz, rep, extra):
    FIX.mkdir(parents=True, exist_ok=True)
    p = FIX / (f"{name}.csv.gz" if gz else f"{name}.csv")
    if gz:
        with gzip.open(p, "wt", encoding="utf-8", newline="\n") as fh:
            out.to_csv(fh, index=False, encoding="utf-8")
    else:
        out.to_csv(p, index=False, encoding="utf-8", lineterminator="\n")
    meta = {"built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "fetcher": "scripts/fetch_macro_series.py", "rows": int(len(out)), "sha256": sha256(p), "gates": rep, "all_gates_pass": True, **extra}
    (FIX / f"{name}.meta.json").write_text(json.dumps(meta, indent=1, default=str), encoding="utf-8")
    log(f"  wrote {p.relative_to(REPO)}: {len(out)} rows, gates green")


def build():
    out, rep = build_hkm(); write_fixture(out, "hkm_factors", True, rep, {"source": HKM_URL.format("{monthly,quarterly}"), "licence": "He, Kelly & Manela: non-commercial use free of charge, as is; NOT committed (gitignored, manifest-registered); cite He, Kelly & Manela (2017, JFE 126(1))",
                                                                          "shape": "TIDY -- freq M or Q; period yyyymm or yyyyq; the four published columns", "vintage": "one file, 2025-06-27; the monthly capital ratio interpolates quarterly balance-sheet data; no vintage history exists",
                                                                          "raw_sha256": {f: sha256(RAW / "hkm" / f"He_Kelly_Manela_Factors_{f}_250627.csv") for f in ("monthly", "quarterly")}})
    out, rep = build_eia(); write_fixture(out, "eia_weekly_stocks", False, rep, {"source": "https://www.eia.gov/opendata/bulk/{PET,NG}.zip (keyless bulk, current vintage, public domain)", "shape": "TIDY -- one row per (series, week_ending); value in kbbl or bcf; release_date_nominal is w+5 (WPSR) / w+6 (WNGSR)",
                                                                                "known_at_rule": "the runner conditions on a week only when week_ending + 7 calendar days <= the month-end session (covers holiday shifts and the June 2022 outage)", "vintage": "current revised values; EIA revises weekly stocks; no vintage archive",
                                                                                "raw_sha256": {z: sha256(RAW / "eia" / f"{z}.zip") for z in ("PET", "NG")}})
    out, rep = build_oecd(); write_fixture(out, "oecd_ir3tib_monthly", False, rep, {"source": OECD_URL, "licence": "OECD data, CC BY 4.0; committed", "shape": "TIDY -- one row per (currency, period YYYY-MM); rate_pct the monthly average 3-month interbank rate, percent per annum",
                                                                                   "use": "at month-end t the value dated t-1 is the last one published (OECD MEI publishes month m in the first half of m+1)", "raw_sha256": sha256(RAW / "oecd" / "ir3tib_monthly.csv")})
    out, rep = build_nass()
    if out is None:
        log(f"  nass: {rep['status']} -- fixture not written")
    else:
        write_fixture(out, "nass_stocks", False, rep, {"source": "USDA NASS Quick Stats (keyed) + ESMIS release archive; public domain; committed", "shape": "TIDY -- one row per (report, commodity, short_desc, obs_date); obs_date is the first-of-month inventory date; release_datetime_utc from ESMIS",
                                                       "attribution": "This product uses the NASS API but is not endorsed or certified by NASS.", "vintage": "current revised values; NASS revises; the release date is the as-released timestamp, the value is not"})


def selftest():
    # HKM
    m = pd.DataFrame({"freq": "M", "period": [201901 + i for i in range(700)], "intermediary_capital_ratio": 0.07, "intermediary_capital_risk_factor": 0.0, "intermediary_value_weighted_investment_return": 0.0, "intermediary_leverage_ratio_squared": 200.0})
    m["period"] = [201001 + (i // 12) * 100 + i % 12 for i in range(700)]; q = pd.DataFrame({"freq": "Q", "period": [20101 + (i // 4) * 10 + i % 4 for i in range(210)], "intermediary_capital_ratio": 0.07, "intermediary_capital_risk_factor": 0.0, "intermediary_value_weighted_investment_return": 0.0, "intermediary_leverage_ratio_squared": 200.0})
    import numpy as np
    rng = np.random.default_rng(1); m["intermediary_capital_ratio"] = 0.05 + 0.04 * rng.random(700); qe = m[m["period"] % 100 % 3 == 0]
    q["intermediary_capital_ratio"] = qe["intermediary_capital_ratio"].to_numpy()[:210] + rng.normal(0, 1e-3, 210)
    base = pd.concat([m, q], ignore_index=True)
    class _G(dict):
        pass
    def g_hkm(df):
        assert not df.duplicated(["freq", "period"]).any(), "G1"; r = df["intermediary_capital_ratio"]; assert ((r > 0) & (r < 1)).all(), "G2"
    g_hkm(base); expect_raise(lambda: g_hkm(pd.concat([base, base.iloc[[0]]])), "a duplicate HKM row (G1)"); bad = base.copy(); bad.loc[0, "intermediary_capital_ratio"] = 1.5; expect_raise(lambda: g_hkm(bad), "a capital ratio above 1 (G2)")
    # EIA
    weeks = pd.date_range("2009-01-02", "2024-06-28", freq="7D"); rows = []
    for s, rel in (("crude_ex_spr", "WPSR"), ("natgas_working_l48", "WNGSR")):
        for w in weeks:
            rows.append({"series": s, "week_ending": w.date().isoformat(), "value": 1000.0, "release_date_nominal": (w + pd.Timedelta(days=EIA_RELEASE_LAG_DAYS[rel])).date().isoformat()})
    e = pd.DataFrame(rows); gates_eia(e); log("  eia gates pass a clean synthetic panel")
    expect_raise(lambda: gates_eia(pd.concat([e, e.iloc[[0]]])), "a duplicate week (G1)"); bad = e.copy(); bad.loc[0, "value"] = 0.0; expect_raise(lambda: gates_eia(bad), "a zero stock (G2)")
    bad = e.copy(); bad.loc[0, "release_date_nominal"] = bad.loc[0, "week_ending"]; expect_raise(lambda: gates_eia(bad), "a release on the week-ending (G4)"); expect_raise(lambda: gates_eia(e.drop(index=[300])), "a missing week (G5)")
    # OECD
    per = pd.period_range("2005-01", "2024-06", freq="M").strftime("%Y-%m"); o = pd.concat([pd.DataFrame({"currency": c, "area": a, "period": per, "rate_pct": 1.0}) for a, c in OECD_AREA.items()], ignore_index=True)
    for (c, p), v in OECD_KNOWN.items():
        o.loc[(o["currency"] == c) & (o["period"] == p), "rate_pct"] = v
    gates_oecd(o); log("  oecd gates pass a clean synthetic panel"); expect_raise(lambda: gates_oecd(o[o["currency"] != "CHF"]), "a missing currency (G2)")
    expect_raise(lambda: gates_oecd(o[~((o["currency"] == "JPY") & (o["period"] == "2015-03"))]), "a missing month (G2)"); bad = o.copy(); bad.loc[(bad["currency"] == "USD") & (bad["period"] == "2019-06"), "rate_pct"] = 2.5; expect_raise(lambda: gates_oecd(bad), "a FRED value not reproduced (G4)")
    # NASS
    n = pd.DataFrame({"report": "grain_stocks", "commodity": "CORN", "short_desc": "CORN, GRAIN - STOCKS, MEASURED IN BU", "obs_date": ["2019-03-01", "2019-06-01", "2019-09-01", "2019-12-01"], "value": [8.6e9, 5.2e9, 2.1e9, 11.4e9], "unit": "BU",
                      "release_datetime_utc": ["2019-03-29T16:00:00Z", "2019-06-28T16:00:00Z", "2019-09-30T16:00:00Z", "2020-01-10T17:00:00Z"]})
    gates_nass(n); log("  nass gates pass a clean synthetic panel"); bad = n.copy(); bad.loc[0, "release_datetime_utc"] = "2019-02-28T16:00:00Z"; expect_raise(lambda: gates_nass(bad), "a release before its observation (G4)")
    bad = n.copy(); bad.loc[3, "release_datetime_utc"] = "2020-03-10T17:00:00Z"; expect_raise(lambda: gates_nass(bad), "a release 100 days after its observation (G4)")
    assert nass_period_to_date(2019, "FIRST OF MAR") == "2019-03-01" and nass_period_to_date(2019, "YEAR") is None
    log("  selftest: every gate passes its clean panel and raises on its break"); return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0]); ap.add_argument("--fetch", choices=["hkm", "eia", "oecd", "esmis", "nass", "all"]); ap.add_argument("--build", action="store_true"); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--probe-nass", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.probe_nass:
        sys.exit(probe_nass())
    if a.fetch:
        for name, fn in (("hkm", fetch_hkm), ("eia", fetch_eia), ("oecd", fetch_oecd), ("esmis", fetch_esmis), ("nass", fetch_nass)):
            if a.fetch in ("all", name):
                fn()
    if a.build:
        build()
    if not (a.fetch or a.build):
        ap.print_help()


if __name__ == "__main__":
    main()
