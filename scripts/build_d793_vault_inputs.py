"""D793's vault inputs: everything `vault_d793_gold_china_open_model.py --vault` reads, into data/joint_run/d793/.
Spec: docs/decisions/D793-PRE-REG-gold-china-open-model-for-the-joint-vault.md §3; JOINT_RUN_CHECKLIST, D793.

    python scripts/build_d793_vault_inputs.py --plan
    python scripts/build_d793_vault_inputs.py --quotes --principals-word "..." --i-accept-the-cost 23
    python scripts/build_d793_vault_inputs.py --verify-quotes
    python scripts/build_d793_vault_inputs.py --link
    python scripts/build_d793_vault_inputs.py --holidays [--dry-run] --principals-word "..."
    python scripts/build_d793_vault_inputs.py --fix      [--dry-run] --principals-word "..."
    python scripts/build_d793_vault_inputs.py --shau     [--dry-run] --principals-word "..."
    python scripts/build_d793_vault_inputs.py --bars     [--dry-run] --principals-word "..." [--accept-end DATE]
    python scripts/build_d793_vault_inputs.py --check

SYSTEM interpreter (databento, pyarrow). This script is NOT hashed by D793's freeze, so writing or fixing it moves
nothing frozen. Each input is built from its own source and must reproduce its committed in-sample rows before it is
written. A --dry-run cuts at 2023-12-31, writes to temp/, and stores nothing dated 2024 or later: it proves the
builder without touching the vault.

PAID DATA. The quotes the subscription does not cover (GC tbbo + bbo-1m, trade dates 2024-01-02 -> 2025-10-02) are
bought on the principal's word ("Yes buy it, and write the input builder", 2026-10-04; priced about USD 22.95, spent
USD 22.13). They are written to data/raw/databento/china_window_2024_2026/ (gitignored, DO NOT DELETE). The
subscription's free window is the TRAILING TWELVE MONTHS, so it moves daily: on 2026-10-04 it covered 2025-10-03
onward at USD 0.00 (get_cost). The first run assumed 2025-09-11; the guard below refused the 32 windows of
2025-09-11 -> 10-02 at USD 1.08, and they were bought inside the approval. The covered files go to the same
directory, and the committed manifest
is data/china_window_2024_2026_manifest.csv. data/joint_run/d793/paid/ holds HARD LINKS to these files and to the
2016-2023 paid files. Nothing is moved, and no link is written through.

The files' CONTENTS are not read here: only their record timestamps are checked against their windows (as the 2016-23
fetcher checked its own). The vault reads them once, in --vault.
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures as cf
import csv
import datetime as dt
import json
import os
import re
import stat
import subprocess
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
MAIN = Path("C:/Users/O/Desktop/Projects/Backtest Framework")
JR = MAIN / "data" / "joint_run" / "d793"
BUY = MAIN / "data" / "raw" / "databento" / "china_window_2024_2026"
INSAMPLE_PAID = MAIN / "data" / "raw" / "databento" / "china_window_2016_2023"
MANIFEST = REPO / "data" / "china_window_2024_2026_manifest.csv"
LOCK = BUY / ".download.lock"
DRY = REPO / "temp" / "d793_inputs_dry"
FIRST, VAULT_END = "2024-01-02", "2026-09-18"
SUB_FROM = "2025-10-03"                     # the subscription's trailing-12-month free window on 2026-10-04 (get_cost 0.00)
APPROVED_USD, CAP_USD = 23.0, 28.0
THREADS, MAX_ERRORS = 8, 20
JOBS = (("GC.v.0", "tbbo"), ("GC.v.0", "bbo-1m"))
UA = "Backtest-Framework research script (one-off historical fetch)"
XSHG_COMMIT = "20ed473663277e15285d8433c0c80b580aa4c4c8"   # the committed calendar's own source commit (2026-01-07)
XSHG_API = ("https://api.github.com/repos/gerrymanoim/exchange_calendars/contents/exchange_calendars/"
            f"exchange_calendar_xshg.py?ref={XSHG_COMMIT}")
XSHG_URL = ("https://github.com/gerrymanoim/exchange_calendars/blob/" + XSHG_COMMIT +
            "/exchange_calendars/exchange_calendar_xshg.py")
SHAU_URL = "https://en.sge.com.cn/graph/DayilyJzj?start=2016-01-01&end=2026-09-18"
CAL = REPO / "data" / "calendar" / "china_exchange_holidays.csv"
FIX = REPO / "data" / "fixtures" / "cny_central_parity.csv"
SHAU = REPO / "data" / "fixtures" / "sge_shau_benchmark_2016_2023.csv"
BJ = dt.timezone(dt.timedelta(hours=8))
DRY_CUT = "2023-12-31"


class D793InputError(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D793InputError(msg)


def word_or_dry(word: str | None, dry: bool) -> None:
    need(dry or bool(word and word.strip()), "a vault input needs --principals-word, or --dry-run (cut at 2023-12-31)")


def out_dir(dry: bool) -> Path:
    d = DRY if dry else JR
    d.mkdir(parents=True, exist_ok=True)
    return d


# ================================================================================ quotes: buy / fetch, link, verify
def window(day: str) -> tuple[str, str]:
    """The 2016-23 purchase's window: 18:30 ET on the evening before -> 03:15 ET on the trade date."""
    import fetch_china_window_tbbo as F
    d = dt.date.fromisoformat(day)
    a = dt.datetime.combine(d - dt.timedelta(days=1), dt.time(18, 30), tzinfo=F.NY).astimezone(dt.timezone.utc)
    b = dt.datetime.combine(d, dt.time(3, 15), tzinfo=F.NY).astimezone(dt.timezone.utc)
    return a.isoformat(), b.isoformat()


def rel_path(sym: str, sch: str, day: str) -> Path:
    return Path(f"{sym.split('.')[0]}_{sch}") / day[:4] / f"{day}.dbn.zst"


def plan_rows() -> list[tuple[str, str, str]]:
    return [(sym, sch, d.strftime("%Y-%m-%d")) for sym, sch in JOBS for d in pd.bdate_range(FIRST, VAULT_END)]


def load_manifest() -> dict[str, dict[str, str]]:
    if not MANIFEST.exists():
        return {}
    with open(MANIFEST, encoding="utf-8", newline="") as fh:
        return {r["path"]: r for r in csv.DictReader(fh)}


def write_manifest(rows: dict[str, dict[str, str]]) -> None:
    import fetch_china_window_tbbo as F
    tmp = MANIFEST.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=F.FIELDS, lineterminator="\n")
        w.writeheader()
        for k in sorted(rows):
            w.writerow(rows[k])
    os.replace(tmp, MANIFEST)


def quotes(word: str | None, accepted: float | None) -> int:
    """Buy (2024-01-02 -> 2025-10-02) and fetch (2025-10-03 -> 2026-09-18, covered) GC tbbo + bbo-1m, GC.v.0."""
    import databento as db
    import fetch_china_window_tbbo as F
    need(bool(word and word.strip()), "the purchase needs --principals-word")
    need(accepted is not None and abs(accepted - APPROVED_USD) <= 0.5,
         f"refused: pass --i-accept-the-cost {APPROVED_USD:g} (the principal's approval)")
    BUY.mkdir(parents=True, exist_ok=True)
    (BUY / "DO_NOT_DELETE.md").write_text(
        "# DO NOT DELETE — PAID DATA (about USD 23, bought 2026-10-04)\n\nGC tbbo + bbo-1m for gold's China window, "
        "trade dates 2024-01-02 -> 2026-09-18 (2024-01-02 -> 2025-10-02 bought; 2025-10-03 on covered by the CME "
        "subscription), for D793's vault read. Bought on the principal's word (\"Yes buy it, and write the input "
        "builder\"). Read only by `vault_d793_gold_china_open_model.py --vault`. The manifest is "
        "data/china_window_2024_2026_manifest.csv. CME terms forbid committing these files.\n", encoding="utf-8")
    need(not LOCK.exists(), f"another downloader holds {LOCK}; refusing")
    LOCK.write_text(str(os.getpid()), encoding="utf-8")
    try:
        c = db.Historical(F.api_key())
        done = load_manifest()
        rows = dict(done)
        spent = sum(float(r["usd"]) for r in done.values())
        todo = [r for r in plan_rows() if rel_path(*r).as_posix() not in done]
        print(f"{len(todo)} windows to fetch; spent so far USD {spent:.2f}; approved {APPROVED_USD}, cap {CAP_USD}", flush=True)
        lock = threading.Lock()
        st = {"spent": spent, "stop": False, "n": 0, "empty": 0}
        errors: list[str] = []

        def one(r: tuple[str, str, str]) -> None:
            sym, sch, day = r
            if st["stop"]:
                return
            try:
                s, e = window(day)
                kw = dict(dataset=F.DATASET, symbols=[sym], schema=sch, start=s, end=e, stype_in="continuous")
                try:
                    usd = float(F.retry(c.metadata.get_cost, **kw))
                except Exception as ex:  # noqa: BLE001
                    if "symbology_invalid_request" in str(ex):
                        with lock:
                            st["empty"] += 1
                        return
                    raise
                if day >= SUB_FROM:
                    need(usd == 0.0, f"{day} {sch}: the subscription window priced at USD {usd} (expected 0)")
                with lock:
                    if st["spent"] + usd > CAP_USD:
                        st["stop"] = True
                        print(f"CAP: {day} {sch} would bring the total to USD {st['spent'] + usd:.2f}; stopping", flush=True)
                        return
                    st["spent"] += usd
                out = BUY / rel_path(sym, sch, day)
                out.parent.mkdir(parents=True, exist_ok=True)
                tmp = out.with_suffix(".part")
                if not out.exists():
                    store = F.retry(c.timeseries.get_range, **kw)
                    tmp.unlink(missing_ok=True)
                    store.to_file(str(tmp))
                    del store
                    F.count_records(tmp, s, e)                       # timestamps only: every record inside its window
                    os.replace(tmp, out)
                    os.chmod(out, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
                recs = F.count_records(out, s, e)
                row = {"path": rel_path(sym, sch, day).as_posix(), "symbol": sym, "schema": sch, "day": day,
                       "start_utc": s, "end_utc": e, "bytes": str(out.stat().st_size), "usd": f"{usd:.6f}",
                       "records": str(recs), "sha256": F.sha256(out),
                       "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
                with lock:
                    rows[row["path"]] = row
                    st["n"] += 1
                    if st["n"] % 100 == 0:
                        print(f"  {st['n']} fetched, USD {st['spent']:.2f}, last {day} {sch}", flush=True)
                        write_manifest(rows)
            except Exception as ex:  # noqa: BLE001
                with lock:
                    errors.append(f"{r}: {type(ex).__name__}: {str(ex)[:200]}")
                    print("ERROR", errors[-1], flush=True)
                    if len(errors) >= MAX_ERRORS:
                        st["stop"] = True

        with ThreadPoolExecutor(THREADS) as ex:
            list(ex.map(one, todo))
        write_manifest(rows)
        bought = sum(float(r["usd"]) for r in rows.values())
        print(f"done: {st['n']} files, {st['empty']} windows with no session, {len(errors)} errors; total USD {bought:.2f}"
              f"{' (STOPPED)' if st['stop'] else ''}", flush=True)
        return 2 if (st["stop"] or errors) else 0
    finally:
        LOCK.unlink(missing_ok=True)


def verify_quotes() -> int:
    import fetch_china_window_tbbo as F
    done = load_manifest()
    bad = [k for k, r in done.items() if not (BUY / k).exists() or str((BUY / k).stat().st_size) != r["bytes"]
           or F.sha256(BUY / k) != r["sha256"]]
    usd = sum(float(r["usd"]) for r in done.values())
    by = pd.DataFrame(done.values()).groupby("schema").agg(files=("path", "size"), first=("day", "min"), last=("day", "max"))
    print(by.to_string())
    print(f"{len(done)} files, USD {usd:.2f}, {len(bad)} mismatches {bad[:5]}")
    return 1 if bad else 0


def link() -> int:
    """Hard links (never copies, never moves) of the 2016-23 and 2024-26 paid files into JR/paid in D770's layout."""
    dst = JR / "paid"
    n = 0
    for src_root in (INSAMPLE_PAID, BUY):
        for p in src_root.rglob("*.dbn.zst"):
            rel = p.relative_to(src_root)
            q = dst / rel
            if q.exists():
                need(os.path.samefile(p, q), f"{q} exists and is not a link to {p}")
                continue
            q.parent.mkdir(parents=True, exist_ok=True)
            os.link(p, q)
            n += 1
    print(f"linked {n} new files into {dst}", flush=True)
    return 0


# ================================================================================ holidays
def holidays(word: str | None, dry: bool) -> int:
    word_or_dry(word, dry)
    req = urllib.request.Request(XSHG_API, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        src = base64.b64decode(json.loads(r.read().decode("utf-8"))["content"]).decode("utf-8")
    m = re.search(r"precomputed_shanghai_holidays\s*=\s*pd\.to_datetime\(\s*\[(.*?)\]", src, flags=re.S)
    need(m is not None, "the XSHG source has no precomputed_shanghai_holidays list")
    dates = sorted({d for d in re.findall(r"[\"'](\d{4}-\d\d-\d\d)[\"']", m.group(1))})
    cut = DRY_CUT if dry else VAULT_END
    wk = [d for d in dates if "2016-01-01" <= d <= cut and dt.date.fromisoformat(d).weekday() < 5]
    with open(CAL, encoding="utf-8", newline="") as fh:
        committed = list(csv.DictReader(fh))
    old = [r["date"] for r in committed]
    need([d for d in wk if d < "2024-01-01"] == old, "identity: the source's 2016-2023 weekday holidays differ from the "
                                                     "committed calendar")
    new = [d for d in wk if d >= "2024-01-01"]
    need(dry or (new and max(new) >= "2025-10-01"), "the source does not reach 2025's National Day: it cannot cover the vault")
    blk = max(int(r["block"]) for r in committed)
    rows = [dict(r) for r in committed]
    prev = None
    today = dt.date.today().isoformat()
    for d in new:
        if prev is None or (dt.date.fromisoformat(d) - dt.date.fromisoformat(prev)).days > 4:
            blk += 1
        rows.append({"date": d, "weekday": dt.date.fromisoformat(d).strftime("%a"), "block": str(blk),
                     "source_url": XSHG_URL, "accessed_date": today})
        prev = d
    out = out_dir(dry) / "china_exchange_holidays.csv"
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(committed[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"holidays: {len(old)} committed rows reproduced; {len(new)} new rows to {cut}; -> {out}", flush=True)
    return 0


# ================================================================================ the CNY fix
def fix(word: str | None, dry: bool) -> int:
    import build_cny_fix as BF
    import fetch_cny_fix as FF
    import urllib.parse
    word_or_dry(word, dry)
    head0, body23 = BF.parse_safe(BF.RAW / "safe_central_parity_2023.html")
    committed = pd.read_csv(FIX, dtype=str, encoding="utf-8")
    c23 = committed[committed["date"].str[:4] == "2023"]
    need([r[0] for r in sorted(body23)] == c23["date"].tolist(), "identity: the parser's 2023 dates differ")
    for r, (_, cr) in zip(sorted(body23), c23.iterrows()):
        need(f"{float(r[1]) / 100.0:.4f}" == cr["usdcny_fix"] and list(r[1:]) == cr.iloc[2:].tolist(),
             f"identity: the parser's 2023 row {r[0]} differs from the committed fixture")
    new: dict[str, list[str]] = {}
    if not dry:
        raw = JR / "raw_cny_fix"
        raw.mkdir(parents=True, exist_ok=True)
        for year, end in ((2024, "2024-12-31"), (2025, "2025-12-31"), (2026, VAULT_END)):
            p = raw / f"safe_central_parity_{year}.html"
            if not p.exists():
                form = urllib.parse.urlencode({"startDate": f"{year}-01-01", "endDate": end, "queryYN": "true"}).encode()
                p.write_bytes(FF.fetch(FF.SAFE, data=form))
                time.sleep(FF.PAUSE)
            head, body = BF.parse_safe(p)
            need(head == head0, f"{p.name}: the header differs from 2023's")
            for r in body:
                if "2024-01-01" <= r[0] <= VAULT_END:
                    new[r[0]] = r
    out = out_dir(dry) / "cny_central_parity.csv"
    lines = FIX.read_text(encoding="utf-8").splitlines()               # the committed rows, verbatim as text
    for d in sorted(new):
        r = new[d]
        usd = float(r[1]) / 100.0
        need(5.5 < usd < 8.0, f"{d}: USD/CNY fix {usd} out of range")
        lines.append(",".join([d, f"{usd:.4f}"] + r[1:]))
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    back = pd.read_csv(out, dtype=str, encoding="utf-8")
    need(back.iloc[: len(committed)].equals(committed), "identity: the written file's committed rows differ")
    print(f"fix: the parser reproduces 2023 ({len(c23)} rows); {len(new)} new rows -> {out}", flush=True)
    return 0


# ================================================================================ the SGE SHAU benchmark
def shau(word: str | None, dry: bool) -> int:
    word_or_dry(word, dry)
    raw = subprocess.run(["curl", "-s", SHAU_URL], capture_output=True, check=True).stdout   # curl's own UA, as in 2026-10-03
    obj = json.loads(raw.decode("utf-8"))
    del raw
    need(set(obj) == {"zp", "wp"}, f"unexpected SGE reply keys {set(obj)}")
    cut = dt.date.fromisoformat(DRY_CUT if dry else VAULT_END)

    def keep(series: list[list[float]]) -> dict[dt.date, float]:
        out: dict[dt.date, float] = {}
        for ts, val in series:
            d = dt.datetime.fromtimestamp(ts / 1000, tz=BJ).date()
            if d > cut:
                continue                                         # discarded at decode; never stored
            need(d not in out, f"duplicate date {d}")
            out[d] = val
        return out
    am, pm = keep(obj["zp"]), keep(obj["wp"])
    del obj
    dates = sorted(set(am) | set(pm))
    rows = [(d.isoformat(), "" if am.get(d) is None else repr(float(am[d])), "" if pm.get(d) is None else repr(float(pm[d])))
            for d in dates]
    committed = pd.read_csv(SHAU, dtype=str, encoding="utf-8", keep_default_na=False)
    mine = pd.DataFrame(rows, columns=list(committed.columns))
    need(mine[mine["date_beijing"] < "2024-01-01"].reset_index(drop=True).equals(committed),
         "identity: the endpoint's 2016-2023 rows differ from the committed fixture, as text")
    out = out_dir(dry) / "sge_shau_benchmark.csv"
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(list(committed.columns))
        w.writerows(rows)
    print(f"shau: {len(committed)} committed rows reproduced as text; {len(mine) - len(committed)} new rows to {cut} -> {out}",
          flush=True)
    return 0


# ================================================================================ the bars (D765's extractor)
_BARS_CFG: dict[str, Any] | None = None


def _bars_patch(cfg: dict[str, Any]) -> None:
    import stage0_d765_china_open as C
    global _BARS_CFG
    _BARS_CFG = cfg
    C.SEAL = cfg["seal"]
    C.SEAL_NS = int(pd.Timestamp(cfg["seal"], tz="UTC").value)
    C.TMP = Path(cfg["tmp"])
    C.ProcessPoolExecutor = _BarsPool


class _BarsPool(cf.ProcessPoolExecutor):
    def __init__(self, max_workers: int | None = None, *a: Any, **kw: Any) -> None:
        need(_BARS_CFG is not None, "the bars pool needs its patch")
        super().__init__(max_workers, initializer=_bars_patch, initargs=(_BARS_CFG,))


def bars(word: str | None, dry: bool, accept_end: str | None) -> int:
    import stage0_d765_china_open as C
    word_or_dry(word, dry)
    end = DRY_CUT if dry else VAULT_END
    seal = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    if dry:
        seal = "2024-01-01"
    tmp = out_dir(dry) / "d765_cache"
    _bars_patch({"seal": seal, "tmp": str(tmp)})
    rc = C.extract()
    need(rc in (0, None), "D765's extract failed")
    ref_dir = REPO / "temp" / "d765"
    for r in C.ROOTS:
        new = pd.read_parquet(tmp / f"raw_{r}.parquet")
        ref = pd.read_parquet(ref_dir / f"raw_{r}.parquet")
        part = new[new["day"] < "2024-01-01"].reset_index(drop=True)
        need(part.equals(ref), f"identity: {r}'s rebuilt minutes to 2023 differ from D765's cache")
        last = str(new["day"].max())
        if not dry:
            need(last >= VAULT_END or (accept_end is not None and last >= accept_end),
                 f"{r}'s bars end {last}, before {VAULT_END} (the 10-09 top-up?); --accept-end is the principal's call")
        print(f"bars {r}: {len(ref):,} in-sample minutes reproduced; {len(new) - len(part):,} after; last day {last}", flush=True)
    return 0


# ================================================================================ check and plan
def check() -> int:
    missing = [k for k in ("d765_cache", "china_exchange_holidays.csv", "cny_central_parity.csv", "sge_shau_benchmark.csv",
                           "paid") if not (JR / k).exists()]
    print("missing:", missing or "none")
    m = load_manifest()
    days = {r["day"] for r in m.values()}
    want = {d for _, _, d in plan_rows()}
    print(f"quotes: {len(m)} manifest rows over {len(days)} days (planned {len(want)})")
    return 1 if missing else 0


def plan() -> int:
    rows = plan_rows()
    print(f"quotes: {len(rows)} windows ({len(rows) // 2} trade dates x 2 schemas); bought before {SUB_FROM}, covered after")
    print(f"vault directory {JR}; paid cache {BUY}; manifest {MANIFEST.relative_to(REPO)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    for f in ("plan", "quotes", "verify-quotes", "link", "holidays", "fix", "shau", "bars", "check", "dry-run"):
        ap.add_argument(f"--{f}", action="store_true")
    ap.add_argument("--principals-word", default=None)
    ap.add_argument("--i-accept-the-cost", type=float, default=None)
    ap.add_argument("--accept-end", default=None)
    a = ap.parse_args(argv)
    if a.plan:
        return plan()
    if a.quotes:
        return quotes(a.principals_word, a.i_accept_the_cost)
    if a.verify_quotes:
        return verify_quotes()
    if a.link:
        return link()
    if a.holidays:
        return holidays(a.principals_word, a.dry_run)
    if a.fix:
        return fix(a.principals_word, a.dry_run)
    if a.shau:
        return shau(a.principals_word, a.dry_run)
    if a.bars:
        return bars(a.principals_word, a.dry_run, a.accept_end)
    if a.check:
        return check()
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
