"""D406 SCREEN -- open-interest density at spot. The bar was committed in 478fb72 BEFORE this ran.

    uv run python scripts/run_d406_oi_density_screen.py --screen

A PRE-SCREEN, not a study. Nothing is scored into a book. D263's inversion.

THE BAR, from the record section 5, unchanged:
  T1  mean |forward move| monotone DECREASING across Q1->Q5 of density
  T2  Q5 - Q1 at least 10% of the pooled mean |move|, in that direction
  T3  T1 SURVIVES WITHIN VOLATILITY TERCILES        <- the most likely killer
  5b  signed forward return reported, CANNOT CLEAR (no direction was declared)

TWO PRICE BASES, and getting this wrong is the D403 trap. STRIKES ARE AS TRADED; the daily
fixture is SPLIT-ADJUSTED. So levels use RAW_CLOSE = CLOSE * raw_price_factor and returns use
the adjusted series (a ratio inside one basis is basis-invariant). [ALIGN] proves the level
basis by an INDEPENDENT estimate of spot taken from the options data itself -- the strike whose
call delta sits nearest 0.5.
"""
import argparse
import gzip
import importlib.util
import json
import os
import pathlib
import sys
import time
from collections import Counter

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]

_OPENED = dict(n=0, refused=0)


def _audit(event, args):
    if event != "open":
        return
    p = args[0]
    if isinstance(p, bytes):
        p = p.decode(errors="replace")
    elif not isinstance(p, (str, os.PathLike)):
        return
    low = os.fspath(p).replace("\\", "/").lower()
    _OPENED["n"] += 1
    if "holdout" in low:
        _OPENED["refused"] += 1
        raise RuntimeError(f"[SPLIT] refused to open {low}")


sys.addaudithook(_audit)


def _load(name, fname):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fname)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


sys.path.insert(0, str(REPO / "src"))
RP = _load("rp", "ragged_panel.py")
X = _load("d320", "run_d320_tilt_filters.py")
UF = _load("d339", "d339_universe_floor.py")
UF.bind(X, None)

CACHE = REPO / "data" / "raw" / "alphavantage" / "options"
MANIFEST = CACHE / "_manifest.json"
FIX = REPO / "data/fixtures/us_shorts_daily_raw.csv.gz"
EVJ = REPO / "data/fixtures/us_shorts_daily_raw_events.json"
DERIV = REPO / "temp" / "d406_chain_summary.json"
OUT = REPO / "data" / "d406_oi_density_screen.json"

WS = (1.0, 0.5, 2.0)          # window half-width in the name's own daily sigma; 1.0 primary
MIN_DENSE_STRIKES = 10        # a four-strike ladder has no density
MIN_OI = 100
MIN_NAMES = 50                # per snapshot, for quintiles to mean anything
NQ = 5
HL_VOL = 63
T2_BAR = 0.10


# ------------------------------------------------------------------ chain summaries
def summarise_chains(verbose=True):
    """Per (symbol, date): the strike axis with calls+puts OI summed, plus the delta-0.5 spot.

    CALLS AND PUTS ARE SUMMED AND NEVER NETTED -- section 4. A signed aggregate is dealer
    gamma, which requires assuming customers are net long calls and short puts, and inference
    is what this line keeps dying of."""
    if DERIV.exists():
        return json.loads(DERIV.read_text(encoding="utf-8"))
    t0 = time.time()
    out, n = {}, 0
    for sd in sorted(CACHE.iterdir()):
        if not sd.is_dir():
            continue
        for f in sorted(sd.glob("*.json.gz")):
            try:
                with gzip.open(f, "rt", encoding="utf-8") as fh:
                    rows = json.load(fh).get("data") or []
            except (OSError, EOFError, json.JSONDecodeError):
                continue
            oi, dl = {}, []
            for r in rows:
                try:
                    k = float(r["strike"])
                    v = float(r.get("open_interest") or 0)
                except (KeyError, TypeError, ValueError):
                    continue
                oi[k] = oi.get(k, 0.0) + v
                if str(r.get("type", "")).lower() == "call":
                    try:
                        dl.append((abs(float(r["delta"]) - 0.5), k))
                    except (KeyError, TypeError, ValueError):
                        pass
            if not oi:
                continue
            ks = np.array(sorted(oi))
            vs = np.array([oi[k] for k in ks])
            # f.stem on "2023-11-15.json.gz" leaves "2023-11-15.json" -- Path.stem strips ONE
            # suffix. That silently made every date key unjoinable to the panel, and [ALIGN]
            # caught it by refusing to certify a basis on zero evidence.
            out.setdefault(sd.name, {})[f.name.split(".")[0]] = dict(
                strikes=[float(v) for v in ks], oi=[float(v) for v in vs],
                dense=int((vs >= MIN_OI).sum()), total=float(vs.sum()),
                spot_delta=float(min(dl)[1]) if dl else None)
            n += 1
            if verbose and n % 1500 == 0:
                print(f"    parsed {n:,} chains  {time.time()-t0:.0f}s", flush=True)
    DERIV.parent.mkdir(parents=True, exist_ok=True)
    DERIV.write_text(json.dumps(out), encoding="utf-8")
    if verbose:
        print(f"  parsed {n:,} chains in {time.time()-t0:.0f}s -> {DERIV.name}")
    return out


# ------------------------------------------------------------------ the panel side
def load_panel(verbose=True):
    t0 = time.time()
    panel, cleaned = RP.load_ragged(FIX, EVJ, fee_bps=0.0)
    CLOSE = np.ascontiguousarray(panel.closes.T)
    finT = np.ascontiguousarray(panel.live.T)
    ev = json.loads(EVJ.read_text(encoding="utf-8"))
    RAWF = UF.raw_price_factor(panel, ev)
    VOL = np.full(CLOSE.shape, np.nan)
    pos = {d: i for i, d in enumerate(panel.dates)}
    sym = {s: i for i, s in enumerate(panel.symbols)}
    for s, bars in cleaned.items():
        i = sym.get(s)
        if i is None:
            continue
        for st in bars:
            t = pos.get(st.timestamp[:10])
            if t is not None:
                VOL[t, i] = st.bar.volume
    DV = X.roll_mean_T(CLOSE * VOL)
    keep = UF.floor_mask_v2(CLOSE * RAWF, DV, finT)
    if verbose:
        print(f"  panel {time.time()-t0:.0f}s")
    return dict(panel=panel, dates=list(panel.dates), pos=pos, sym=sym,
                ADJ=CLOSE, RAW=CLOSE * RAWF, live=finT, elig=finT & keep)


def sigma_and_fwd(P):
    """Causal daily EW sigma of ADJUSTED log returns (basis-invariant), and forward |moves|."""
    A = P["ADJ"]
    T, n = A.shape
    lg = np.log(np.where(A > 0, A, np.nan))
    r = np.full((T, n), np.nan)
    r[1:] = lg[1:] - lg[:-1]
    lam = 0.5 ** (1.0 / HL_VOL)
    v = np.full((T, n), np.nan)
    acc = np.zeros(n)
    seen = np.zeros(n, bool)
    for t in range(T):
        x = r[t]
        ok = np.isfinite(x)
        acc = np.where(ok, np.where(seen, lam * acc + (1 - lam) * x * x, x * x), acc)
        seen |= ok
        v[t] = np.where(seen, acc, np.nan)
    return np.sqrt(np.maximum(v, 1e-24)), lg


# ------------------------------------------------------------------ the screen
def set_dates(which):
    """The snapshot dates belonging to ONE set.

    The chain cache under data/raw/ now holds THREE disjoint sets (d406, oos, expiry) in one
    directory tree, so a screen that walked it unfiltered would silently pool 22,672 chains
    instead of its own 7,559 and give a different answer than the one D406 committed. Every
    screen filters to its own manifest."""
    p = CACHE / ("_manifest.json" if which == "d406" else f"_manifest_{which}.json")
    return set(json.loads(p.read_text(encoding="utf-8"))["dates"])


def build_rows(P, chains, sig, lg, w, horizons, allowed=None):
    """One row per (name, snapshot) clearing the density floor, within `allowed` dates."""
    rows = []
    align = []
    for s, byd in chains.items():
        i = P["sym"].get(s)
        if i is None:
            continue
        for d, c in byd.items():
            if allowed is not None and d not in allowed:
                continue
            t = P["pos"].get(d)
            if t is None or c["dense"] < MIN_DENSE_STRIKES or c["total"] <= 0:
                continue
            spot_raw = P["RAW"][t, i]
            if not np.isfinite(spot_raw) or spot_raw <= 0 or not P["elig"][t, i]:
                continue
            if c["spot_delta"]:
                align.append(float(c["spot_delta"] / spot_raw))
            sg = sig[t, i]
            if not np.isfinite(sg) or sg <= 0:
                continue
            ks = np.asarray(c["strikes"]); vs = np.asarray(c["oi"])
            half = w * sg * spot_raw
            inwin = np.abs(ks - spot_raw) <= half
            dens = float(vs[inwin].sum() / c["total"])
            fwd = {}
            for h in horizons:
                u = t + h
                if u < lg.shape[0] and np.isfinite(lg[u, i]) and np.isfinite(lg[t, i]) and P["live"][u, i]:
                    m = float(lg[u, i] - lg[t, i])
                    fwd[h] = (m, abs(m), abs(m) / (sg * np.sqrt(h)))
            if not fwd:
                continue
            rows.append(dict(sym=s, date=d, t=t, i=i, dens=dens, sigma=float(sg),
                             dense=c["dense"], total=c["total"], fwd=fwd))
    return rows, np.array(align)


def quintile_table(rows, h, field, strat=None):
    """Cross-sectional quintiles of `dens` WITHIN each snapshot, pooled. `field` indexes fwd."""
    by = {}
    for r in rows:
        if h in r["fwd"] and (strat is None or strat(r)):
            by.setdefault(r["date"], []).append(r)
    acc = [[] for _ in range(NQ)]
    used = 0
    for d, rs in by.items():
        if len(rs) < MIN_NAMES:
            continue
        used += 1
        v = np.array([r["dens"] for r in rs])
        q = np.quantile(v, np.linspace(0, 1, NQ + 1)); q[-1] += 1e-12
        b = np.clip(np.searchsorted(q, v, side="right") - 1, 0, NQ - 1)
        for j, r in zip(b, rs):
            acc[j].append(r["fwd"][h][field])
    if used < 8 or any(len(a) < 100 for a in acc):
        return None
    means = [float(np.mean(a)) for a in acc]
    ns = [len(a) for a in acc]
    pooled = float(np.mean([x for a in acc for x in a]))
    return dict(snapshots=used, n=ns, means=means, pooled=pooled,
                spread=means[-1] - means[0],
                monotone_dec=bool(all(means[j] >= means[j + 1] for j in range(NQ - 1))),
                monotone_inc=bool(all(means[j] <= means[j + 1] for j in range(NQ - 1))))


def screen(which="d406"):
    t0 = time.time()
    print("D406 SCREEN  open-interest density at spot")
    print("      the bar was committed in 478fb72 BEFORE this ran\n")
    allowed = set_dates(which)
    man = json.loads((CACHE / ("_manifest.json" if which == "d406" else f"_manifest_{which}.json")).read_text(encoding="utf-8"))
    print(f"  manifest {len(man['symbols'])} names x {len(man['dates'])} snapshots, "
          f"fetch stats {man['stats']}")
    chains = summarise_chains()
    P = load_panel()
    sig, lg = sigma_and_fwd(P)
    HZ = (63, 21)                      # ~1 quarter to the next snapshot (primary), 21 bars (shape)

    res = {}
    for w in WS:
        rows, align = build_rows(P, chains, sig, lg, w, HZ, allowed)
        if w == WS[0]:
            med = float(np.median(align)) if align.size else float("nan")
            bad = float(np.mean(np.abs(align - 1.0) > 0.10)) if align.size else float("nan")
            print(f"\n  [ALIGN] delta-0.5 strike / RAW close: n {align.size:,}  median {med:.4f}  "
                  f"off>10% {100*bad:.2f}%")
            assert align.size > 1000, "[ALIGN] too few delta-implied spots to verify the basis"
            assert abs(med - 1.0) < 0.05, (f"[ALIGN] median {med:.4f} -- the strike basis and the "
                                           f"raw close basis disagree")
            print(f"  rows {len(rows):,}  names {len({r['sym'] for r in rows})}  "
                  f"snapshots {len({r['date'] for r in rows})}")
        cell = {}
        for h in HZ:
            # ---- 5a THESIS: forward ABSOLUTE move. Primary is sigma-normalised (field 2),
            #      because raw |move| (field 1) is dominated by volatility and T3 exists to
            #      catch exactly that. BOTH are reported so nothing is selected after the fact.
            for tag, field in (("abs_sigma", 2), ("abs_raw", 1)):
                cell[f"h{h}_{tag}"] = quintile_table(rows, h, field)
            # ---- 5b TRADEABILITY: signed. Reported, CANNOT CLEAR.
            cell[f"h{h}_signed"] = quintile_table(rows, h, 0)
        # ---- T3: within volatility terciles
        sg = np.array([r["sigma"] for r in rows])
        e = np.quantile(sg, [1 / 3, 2 / 3])
        for j, name in enumerate(("lo", "mid", "hi")):
            f = (lambda r, j=j: (r["sigma"] < e[0]) if j == 0 else
                 (e[0] <= r["sigma"] < e[1]) if j == 1 else (r["sigma"] >= e[1]))
            cell[f"h63_abs_sigma_vol_{name}"] = quintile_table(rows, 63, 2, strat=f)
        res[f"w{w}"] = cell
        c = cell["h63_abs_sigma"]
        if c:
            print(f"\n  w={w}  h=63  |move|/sigma by density quintile: "
                  + "  ".join(f"{m:.4f}" for m in c["means"]))
            print(f"        n {c['n']}  snapshots {c['snapshots']}  spread {c['spread']:+.4f}  "
                  f"monotone_dec {c['monotone_dec']}")

    # ---------------- the verdict, against the committed bar ----------------
    prim = res[f"w{WS[0]}"]["h63_abs_sigma"]
    assert prim is not None, "primary cell did not populate"
    T1 = prim["monotone_dec"]
    T2 = (prim["means"][0] - prim["means"][-1]) >= T2_BAR * prim["pooled"]
    terc = {k: res[f"w{WS[0]}"][f"h63_abs_sigma_vol_{k}"] for k in ("lo", "mid", "hi")}
    T3 = all(v is not None and v["monotone_dec"] for v in terc.values())
    print("\n  --- THE BAR (committed 478fb72) ---")
    print(f"    T1 monotone DECREASING           : {T1}")
    print(f"    T2 Q1-Q5 >= 10% of pooled mean   : {T2}   "
          f"({prim['means'][0] - prim['means'][-1]:+.4f} vs {T2_BAR*prim['pooled']:.4f})")
    print(f"    T3 survives within vol terciles  : {T3}")
    for k, v in terc.items():
        if v:
            print(f"       vol {k:3s}  " + "  ".join(f"{m:.4f}" for m in v["means"])
                  + f"   monotone_dec {v['monotone_dec']}  spread {v['spread']:+.4f}")
    sgn = res[f"w{WS[0]}"]["h63_signed"]
    if sgn:
        print(f"\n    5b signed return (REPORTED, CANNOT CLEAR): "
              + "  ".join(f"{m:+.4f}" for m in sgn["means"])
              + f"   spread {sgn['spread']:+.4f}")
    verdict = bool(T1 and T2 and T3)
    print(f"\n  VERDICT: {'CLEARS -- write a pre-registration' if verdict else 'FAILS -- D406 CLOSES'}")
    out_p = OUT if which == "d406" else OUT.with_name(f"d406_oi_density_screen_{which}.json")
    out_p.write_text(json.dumps(dict(snapshot_set=which, bar=dict(T1=T1, T2=T2, T3=T3, clears=verdict),
                                   cells=res, horizons=list(HZ), windows=list(WS)),
                              indent=1, default=float), encoding="utf-8")
    print(f"  wrote {out_p.relative_to(REPO)}  in {time.time()-t0:.0f}s")
    return verdict


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", action="store_true")
    ap.add_argument("--set", default="d406", choices=("d406", "oos", "expiry"))
    a = ap.parse_args()
    if not a.screen:
        ap.error("pass --screen")
    screen(a.set)
