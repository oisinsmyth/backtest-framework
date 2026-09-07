"""D374 -- is the breadth hurdle REACHABLE? H4's names-to-half bar, calibrated against its own nulls.

    uv run python scripts/run_d374_breadth_calibration.py --selftest
    uv run python scripts/run_d374_breadth_calibration.py --observed                          the concentration family, before any null
    uv run python scripts/run_d374_breadth_calibration.py --cells --draws 400 --part 0        A'/B/B_c, ONE cell
    uv run python scripts/run_d374_breadth_calibration.py --report
    --out-dir DIR   (every stage; default data/ -- the smoke runs pass temp/... so nothing under data/ is touched)

Pre-registration: docs/decisions/D374-is-the-breadth-hurdle-reachable.md  (committed 4c0816c, BEFORE this file existed -- R8)

METHODOLOGY, NOT A STRATEGY STUDY. It admits nothing, tests no construction, reads no holdout. Its only product is a verdict on a
hurdle: keep it, replace it, or retire it. Nothing here can be "passed" by a book.

THE PROBLEM. Nothing in this programme has ever cleared the names-to-half-P&L bar -- D371 at 0.8%, D373 at 2.26% against 10%. That is
either a real property of every construction tried here or a bar unreachable by construction, and no study so far can separate them.
H1/H2/H3 are all null-relative; H4 alone is an absolute number, and D373 section 5 says outright its thresholds were "calibrated to
exclude the shape that just failed". So: compute the concentration family PER NULL DRAW and ask what a random book scores.

ONE CELL, NOT FIVE. D373 ran five because it was SELECTING among them and owed a best-of-5 floor. This study selects nothing -- the cell
is inherited -- so no best-of-N floor applies, and imposing one would inflate the null against a decision nobody is taking. Pre-reg s1.

A' IS LOAD-BEARING, REVERSING D373 (where B_c was). The load-bearing control follows the QUESTION: D373 asked whether dip timing beat
cohort membership, so its control re-drew membership; D374 asks whether concentration is mechanical, so its control must hold the name
set EXACTLY fixed and vary only luck. A' is the only arm that does. C is excluded with cause -- randomising direction centres total P&L
at zero, precisely the degenerate case for a share statistic. Pre-reg s3.

THE TAIL DIRECTION INVERTS AND IT IS THE EASIEST THING HERE TO GET WRONG. H1/H2/H3 compare to p95. H4 asks whether a book is
DIVERSIFIED, so concentration is the LOW tail and names_to_half_share compares to p05. [DIR] asserts it against a synthetic one-name
book and a synthetic uniform book, so a p95 typo cannot survive the self-test.

TWO DEFECTS IN THE INCUMBENT IMPLEMENTATION, DECLARED IN THE PRE-REG BEFORE ANY RESULT (s2a):
  (i)  the share statistics are undefined when total P&L <= 0 -- four_groups already returns None. [DEG] excludes those draws from every
       percentile, reports the count beside it, and REFUSES to report an arm whose degenerate share exceeds 20%.
  (ii) names_to_half uses np.searchsorted on a cumulative sum that is NOT monotone: per_name carries negatives, so the descending cumsum
       rises to a peak and falls back. searchsorted requires a sorted array. THIS MAY MEAN D373'S PUBLISHED 18 OF 796 IS WRONG. [MONO]
       recomputes by linear scan and asserts agreement on the observed book; a disagreement is a finding, not a crash.

ASSERTIONS [MIR][CAL][MONO][DIR][DEG][L][S][E][X] -- pre-reg s6. [X] is the one that matters: every audit must RAISE on a deliberately
broken book, or it is worse than none.

Everything shared is imported, not copied: D373's runner whole (and through it d348_prep, run_d359, run_d350/d353/d349/d358).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


V73 = _load("d373r", "run_d373_winners_dip_long.py")        # the cell, the kernel, the controls -- imported, never re-derived
PREP, V59, V58, V50, V47, V53 = V73.PREP, V73.V59, V73.V58, V73.V50, V73.V47, V73.V53
clean = V50.clean
STUDY = 374
DATA = REPO / "data"
SELFTEST_TMP = REPO / "temp" / "d374_selftest"

# The cell is INHERITED from D373, not chosen here. Reordering CELLS in D373 would silently re-point this study, so [MIR] pins the
# ledger by its published numbers rather than by the index alone.
CELL_IX = V73.PRIMARY_IX
CELL = V73.CELLS[CELL_IX]
CELL_NAME = V73.CELL_NAME[CELL_IX]
D373_LEDGER = dict(trades=3932, mean_bp=160.55, median_bp=51.55)          # data/d373_winners_dip_long.json, committed 9162a64
D373_CONC = dict(n_names=796, names_to_half=18, top1=0.05739877589614556, top5=0.20617440690289557, top10=0.3403746465407902)

# The RNG keys are D373's, so a given (arm, draw) is THE SAME DRAW in both studies and the two are directly comparable.
ARM = V73.ARM
DRAWS = dict(A=2000, Bc=2000, B=1000)                                    # pre-reg s3
H4_NAMES_TO_HALF_SHARE = V73.H4_NAMES_TO_HALF_SHARE                      # 0.10, imported so this file cannot disagree with D373's
H4_TOP1_SHARE = V73.H4_TOP1_SHARE                                        # 0.15
H4_TOP5_SHARE = V73.H4_TOP5_SHARE                                        # 0.50
DEGENERATE_MAX = 0.20                                                    # pre-reg s6 [DEG] / s9: refuse to report above this


def out_paths(out_dir):
    d = Path(out_dir)
    return dict(dir=d, observed=d / "d374_observed.json", ctrl=str(d / "d374_ctrl_p{part}.json"),
                report=d / "d374_breadth_calibration.json")


# ------------------------------------------------------------------ the statistic under test
def names_to_half_scan(desc, tot):
    """[MONO] names to half the P&L by EXPLICIT LINEAR SCAN -- the monotone-safe reading of the same definition.

    `desc` is per-name P&L sorted descending; `tot` the book total. The incumbent uses np.searchsorted on cumsum(desc), which is only
    valid if that cumsum is sorted. It is NOT: negative names make it rise to a peak and fall back. This walks it instead, and returns
    the peak so the caller can see how far the hump overshoots.
    """
    if not (tot > 0):
        return None, None, None
    run = 0.0
    hit, peak = None, 0.0
    for i, v in enumerate(desc):
        run += float(v)
        peak = max(peak, run)
        if hit is None and run >= 0.5 * tot:
            hit = i + 1
    return hit, peak, float(np.cumsum(desc).max())


def conc_stats(tr, pnl, P):
    """The concentration family of pre-reg s2, computed identically for the observed book and every null draw.

    Returns None-valued shares when total P&L <= 0 rather than a misleading number -- [DEG] filters on `defined`, it does not patch.
    """
    rows = np.array([t[0] for t in tr]) if len(tr) else np.zeros(0, int)
    per_name = np.bincount(rows, weights=pnl, minlength=P["n"]) if rows.size else np.zeros(P["n"])
    n_names = int((np.bincount(rows, minlength=P["n"]) > 0).sum()) if rows.size else 0
    tot = float(pnl.sum()) if pnl.size else 0.0
    desc = np.sort(per_name)[::-1]
    scan, _peak, cmax = names_to_half_scan(desc, tot)
    search = int(np.searchsorted(np.cumsum(desc), 0.5 * tot) + 1) if tot > 0 else None
    defined = bool(tot > 0 and n_names > 0 and scan is not None)
    return dict(
        trades=int(pnl.size), n_names=n_names, total_pnl_bp=tot, defined=defined,
        names_to_half=scan, names_to_half_searchsorted=search,
        names_to_half_share=(scan / n_names) if defined else None,
        top1_name_share=(float(desc[:1].sum() / tot) if defined else None),
        top5_name_share=(float(desc[:5].sum() / tot) if defined else None),
        top10_name_share=(float(desc[:10].sum() / tot) if defined else None),
        cumsum_peak_over_total=(cmax / tot if defined else None),        # > 1 means the hump the incumbent binary-searches across
    )


def conc_of(res, P):
    return conc_stats(res["trades"], np.asarray(V47.pnl_bp(res), float), P)


# ------------------------------------------------------------------ percentiles, with the degenerate draws named not absorbed
def pct_block(vals, lo_tail=True):
    """[DEG] percentiles over the DEFINED draws only, with the excluded count carried, and a bootstrap SE on each reported percentile.

    `lo_tail` records which tail this statistic is judged on (pre-reg s4). It changes no arithmetic -- p05 and p95 are both reported
    always -- but it is stored in the artifact so the report cannot silently read the wrong end.
    """
    v = np.asarray([x for x in vals if x is not None], float)
    v = v[np.isfinite(v)]
    n_all, n = len(vals), int(v.size)
    if n == 0:
        return dict(n=0, n_draws=n_all, degenerate=n_all, degenerate_share=1.0, judged_on="p05" if lo_tail else "p95")
    rng = np.random.default_rng([V47.SEED, STUDY, 99])
    bs = v[rng.integers(0, n, size=(400, n))]
    return dict(n=n, n_draws=n_all, degenerate=n_all - n, degenerate_share=(n_all - n) / max(1, n_all),
                judged_on="p05" if lo_tail else "p95",
                p05=float(np.percentile(v, 5)), p50=float(np.percentile(v, 50)), p95=float(np.percentile(v, 95)),
                mean=float(v.mean()), min=float(v.min()), max=float(v.max()),
                se_p05=float(np.percentile(bs, 5, axis=1).std(ddof=1)),
                se_p50=float(np.percentile(bs, 50, axis=1).std(ddof=1)),
                se_p95=float(np.percentile(bs, 95, axis=1).std(ddof=1)))


# ------------------------------------------------------------------ [MIR][CAL][MONO][DIR] -- the audits this study specifically needs
def observed_book(P):
    (c, s), (e, cap) = CELL
    return V73.run_long(P, V73.mirror(P, c, s), V59.grids(P)[1], e, cap)


def assert_MIR(P, res):
    """[MIR] the inherited cell reproduces D373's COMMITTED ledger before any null runs. Otherwise this calibrates a different book."""
    pnl = np.asarray(V47.pnl_bp(res), float)
    got = dict(trades=len(res["trades"]), mean_bp=float(pnl.mean()), median_bp=float(np.median(pnl)))
    assert got["trades"] == D373_LEDGER["trades"], f"[MIR] {got['trades']:,} trades != D373's {D373_LEDGER['trades']:,}"
    for k in ("mean_bp", "median_bp"):
        assert abs(got[k] - D373_LEDGER[k]) < 0.01, f"[MIR] {k} {got[k]:+.4f} != D373's {D373_LEDGER[k]:+.2f}"
    return got


def assert_CAL(cs):
    """[CAL] the new concentration function reproduces D373's COMMITTED four_groups values exactly -- it is a re-expression, not a rewrite."""
    assert cs["n_names"] == D373_CONC["n_names"], f"[CAL] n_names {cs['n_names']} != D373's {D373_CONC['n_names']}"
    for k, key in (("top1", "top1_name_share"), ("top5", "top5_name_share"), ("top10", "top10_name_share")):
        assert abs(cs[key] - D373_CONC[k]) < 1e-12, f"[CAL] {key} {cs[key]!r} != D373's {D373_CONC[k]!r}"
    return True


def assert_MONO(cs):
    """[MONO] linear scan vs the incumbent searchsorted, on the observed book. A DISAGREEMENT IS A FINDING, not a crash (pre-reg s2a-ii).

    Returns (agrees, detail). The caller reports it either way; only an impossible value raises.
    """
    scan, search = cs["names_to_half"], cs["names_to_half_searchsorted"]
    assert scan is not None and 1 <= scan <= cs["n_names"], f"[MONO] the scan returned {scan!r} for {cs['n_names']} names"
    d = dict(scan=scan, searchsorted=search, agrees=bool(scan == search),
             d373_published=D373_CONC["names_to_half"], cumsum_peak_over_total=cs["cumsum_peak_over_total"])
    d["d373_correct"] = bool(scan == D373_CONC["names_to_half"])
    return d


def synth_book(P, kind, n_names=100, per_name=10):
    """Two books with KNOWN concentration, for [DIR]. Trade tuples are (row, entry_bar, age, pnl, side); only row is read by conc_stats."""
    tr, pnl = [], []
    for j in range(n_names):
        for i in range(per_name):
            tr.append((j, 100 + i, 40, 0.0, 0))
            pnl.append(100.0 if (kind == "uniform" or j == 0) else 0.0)
    return tr, np.asarray(pnl, float)


def assert_DIR(P):
    """[DIR] the direction of the H4 comparison, proved rather than asserted in prose (pre-reg s4).

    A book concentrated into ONE name must score at the FLOOR of names_to_half_share; a uniform book must score near 0.5. If a p95 were
    used where p05 belongs, the concentrated book would look diversified -- so this checks the ORDER, which no typo can satisfy.
    """
    tr_c, pnl_c = synth_book(P, "onename")
    tr_u, pnl_u = synth_book(P, "uniform")
    c, u = conc_stats(tr_c, pnl_c, P), conc_stats(tr_u, pnl_u, P)
    assert c["names_to_half_share"] == 1 / 100, f"[DIR] the one-name book scored {c['names_to_half_share']!r}, not 1/100"
    assert c["top1_name_share"] == 1.0, f"[DIR] the one-name book's top1 is {c['top1_name_share']!r}, not 1.0"
    assert abs(u["names_to_half_share"] - 0.5) <= 0.01, f"[DIR] the uniform book scored {u['names_to_half_share']!r}, not ~0.5"
    assert c["names_to_half_share"] < u["names_to_half_share"], "[DIR] concentration is not the LOW tail -- the test is inverted"
    return dict(one_name=c["names_to_half_share"], uniform=u["names_to_half_share"])


def assert_DEG(block, arm):
    """[DEG] refuse to report an arm whose degenerate share exceeds 20% (pre-reg s6, s9)."""
    if block.get("degenerate_share", 0.0) > DEGENERATE_MAX:
        return f"REFUSED: {block['degenerate']:,} of {block['n_draws']:,} draws degenerate ({block['degenerate_share']:.1%} > {DEGENERATE_MAX:.0%})"
    return None


# ------------------------------------------------------------------ stages
def prep():
    P = PREP.prep(need_grids=False)
    P["rsi_pct_ok"] = np.isfinite(np.asarray(P["PCT"]["rsi"]))
    P["elig_b"] = np.asarray(P["elig"]) & P["rsi_pct_ok"]
    return P


def stage_observed(P, paths):
    print("\nOBSERVED -- the concentration family, before any null. This adjudicates nothing.")
    t0 = time.time()
    res = observed_book(P)
    mir = assert_MIR(P, res)
    print(f"  [MIR] {CELL_NAME} {mir['trades']:,} trades  mean {mir['mean_bp']:+.2f}  median {mir['median_bp']:+.2f}  == D373's committed ledger")
    cs = conc_of(res, P)
    assert_CAL(cs)
    print(f"  [CAL] n_names {cs['n_names']}, top1/5/10 {cs['top1_name_share']:.4f}/{cs['top5_name_share']:.4f}/{cs['top10_name_share']:.4f}  == D373's four_groups")
    mono = assert_MONO(cs)
    print(f"  [MONO] scan {mono['scan']}  searchsorted {mono['searchsorted']}  D373 published {mono['d373_published']}  "
          f"-> {'AGREE' if mono['agrees'] else '*** DISAGREE ***'}   cumsum peak / total {cs['cumsum_peak_over_total']:.3f}")
    d = assert_DIR(P)
    print(f"  [DIR] one-name book {d['one_name']:.4f} < uniform book {d['uniform']:.4f} -- concentration is the LOW tail")
    out = dict(study=STUDY, kind="METHODOLOGY -- adjudicates a hurdle, not a strategy", cell=CELL_NAME,
               ledger=mir, observed=cs, mono=mono, dir_check=d, rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["observed"].write_text(json.dumps(clean(out)))              # [P] persist before rendering
    print(f"  wrote {paths['observed']}")
    print(f"\n  names to half {cs['names_to_half']} of {cs['n_names']} = {cs['names_to_half_share']:.4%}  (bar {H4_NAMES_TO_HALF_SHARE:.0%})")
    print(f"  ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return out


def stage_cells(P, draws, part, paths):
    """A'/B/B_c on ONE cell. No best-of-N floor: nothing is being selected (pre-reg s1)."""
    print(f"\nCONTROLS -- {draws} draws x 1 cell ({CELL_NAME}), part {part}.  NO best-of-N floor: nothing is selected here.")
    (c, s), (e, cap) = CELL
    elig, sc = np.asarray(P["elig"]), V59.grids(P)[1]
    sig, coh = V73.mirror(P, c, s), V73.top_cohort(P, c)
    res = observed_book(P)
    assert_MIR(P, res)
    obs = conc_of(res, P)
    assert_CAL(obs)
    print(f"  [MIR][CAL] observed: {obs['trades']:,} trades, {obs['n_names']} names, "
          f"names_to_half_share {obs['names_to_half_share']:.4%}")
    PB = V53.b_pool_P(P, P["elig_b"])
    A, B, BC = [], [], []
    t0 = time.time()
    for d in range(part * draws, (part + 1) * draws):
        sA, scA = V73.aprime_draw_long(sig, sc, elig, V73.draw_rng(d, "A"))
        A.append(conc_of(V73.run_long(P, sA, scA, e, cap), P))
        sBc, kc = V73.bc_long(sig, coh, elig, V73.draw_rng(d, "Bc"))
        V59.assert_Bc(sBc, sig, coh, elig, kc)
        BC.append(conc_of(V73.run_long(P, sBc, sc, e, cap), P))
        if d < part * draws + (draws + 1) // 2:                        # B at half the count, as pre-registered
            sB = V47.control_b_signal(PB, sig, V73.draw_rng(d, "B"))
            V58.assert_B(P, PB, sig, sB, elig)
            B.append(conc_of(V73.run_long(P, sB, sc, e, cap), P))
        n = d - part * draws + 1
        if n % 10 == 0 or n == draws:
            print(f"    {n}/{draws} ({time.time() - t0:.0f}s, {(time.time() - t0) / n:.2f} s/draw)  {PREP.rss_line()}", flush=True)
    out = dict(study=STUDY, draws=draws, part=part, cell=CELL_NAME, observed=obs,
               control_A_prime=A, control_B=B, control_B_c=BC,
               rng="D373's keys: default_rng([SEED, 373, ARM, draw]) -- a given (arm, draw) is THE SAME DRAW in both studies",
               seconds_per_draw=(time.time() - t0) / max(draws, 1), rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    f = Path(paths["ctrl"].format(part=part))
    f.write_text(json.dumps(clean(out)))                               # [P] persist before rendering
    print(f"  wrote {f} ({time.time() - t0:.0f}s)")
    return out


def load_controls(paths):
    fs = sorted(paths["dir"].glob("d374_ctrl_p*.json"))
    if not fs:
        return None
    parts = [json.loads(f.read_text()) for f in fs]
    seen = {p["part"] for p in parts}
    assert len(seen) == len(parts), f"[CTRL] duplicate parts in {[f.name for f in fs]}"
    out = dict(parts=[dict(file=f.name, part=p["part"], draws=p["draws"], seconds_per_draw=p["seconds_per_draw"])
                      for f, p in zip(fs, parts)], observed=parts[0]["observed"])
    for arm in ("control_A_prime", "control_B", "control_B_c"):
        out[arm] = [d for p in parts for d in p[arm]]
    return out


def stage_report(P, paths):
    print("\nREPORT")
    t0 = time.time()
    ctrl = load_controls(paths)
    assert ctrl, "[CTRL] no d374_ctrl_p*.json -- run --cells first"
    res = observed_book(P)
    assert_MIR(P, res)
    obs = conc_of(res, P)
    assert_CAL(obs)
    mono = assert_MONO(obs)
    dirc = assert_DIR(P)

    arms = dict(A="control_A_prime", B="control_B", Bc="control_B_c")
    # names_to_half_share is judged on the LOW tail; the top-k shares on the HIGH tail. Pre-reg s4.
    stats = dict(names_to_half_share=True, top1_name_share=False, top5_name_share=False, top10_name_share=False)
    blocks, refusals = {}, {}
    for a, key in arms.items():
        blocks[a] = {st: pct_block([d[st] for d in ctrl[key]], lo_tail=lo) for st, lo in stats.items()}
        r = assert_DEG(blocks[a]["names_to_half_share"], a)
        if r:
            refusals[a] = r

    A = blocks["A"]["names_to_half_share"]
    K1 = dict(question="is the 10% bar reachable by a random book with this exact name set?",
              arm="A_prime", p50=A.get("p50"), se_p50=A.get("se_p50"), bar=H4_NAMES_TO_HALF_SHARE,
              reachable=(None if "p50" not in A else bool(A["p50"] >= H4_NAMES_TO_HALF_SHARE)),
              verdict=("UNRESOLVED" if "p50" not in A or "A" in refusals else
                       ("BAR REACHABLE -- D373's failure carries information" if A["p50"] >= H4_NAMES_TO_HALF_SHARE
                        else "BAR UNREACHABLE -- RETIRE the absolute bar")),
              other_arms={a: blocks[a]["names_to_half_share"].get("p50") for a in ("B", "Bc")})
    K2 = dict(question="is the observed book more concentrated than luck, for its own name set?",
              observed=obs["names_to_half_share"], arm="A_prime", p05=A.get("p05"), se_p05=A.get("se_p05"),
              verdict=("UNRESOLVED" if "p05" not in A or "A" in refusals else
                       ("CONCENTRATED -- below its own null's p05" if obs["names_to_half_share"] < A["p05"]
                        else "NOT CONCENTRATED -- inside its own null; D373's H4 FAIL was the bar's doing")))
    K3 = {}
    for st, bar in (("top1_name_share", H4_TOP1_SHARE), ("top5_name_share", H4_TOP5_SHARE)):
        b = blocks["A"][st]
        K3[st] = dict(observed=obs[st], bar=bar, p50=b.get("p50"), p95=b.get("p95"), se_p95=b.get("se_p95"),
                      bar_failable=(None if "p95" not in b else bool(b["p95"] > bar)),
                      observed_above_p95=(None if "p95" not in b else bool(obs[st] > b["p95"])))
    K4 = dict(replacement="names_to_half_share >= A' p05 on the study's own ledger; top1/top5 name share <= their A' p95; "
                          "degenerate-draw count reported alongside",
              applies=(K1["verdict"].startswith("BAR UNREACHABLE")),
              thresholds_for_this_ledger=dict(names_to_half_share_p05=A.get("p05"),
                                              top1_name_share_p95=blocks["A"]["top1_name_share"].get("p95"),
                                              top5_name_share_p95=blocks["A"]["top5_name_share"].get("p95")))
    preds = score_predictions(obs, blocks, mono, K1, K2)
    out = dict(study=STUDY, kind="METHODOLOGY -- adjudicates a hurdle, not a strategy", cell=CELL_NAME,
               observed=obs, mono=mono, dir_check=dirc,
               controls=dict(parts=ctrl["parts"], draws={a: len(ctrl[k]) for a, k in arms.items()},
                             floor="NONE -- nothing is selected (pre-reg s1)"),
               nulls=blocks, refusals=refusals, K1=K1, K2=K2, K3=K3, K4=K4, predictions=preds, rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(clean(out)))                 # [P] PERSIST BEFORE RENDERING
    print(f"  wrote {paths['report']}")
    print_report(out)
    print(f"  ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return out


def score_predictions(obs, blocks, mono, K1, K2):
    A = blocks["A"]
    p50, p05 = A["names_to_half_share"].get("p50"), A["names_to_half_share"].get("p05")
    t1 = A["top1_name_share"].get("p50")
    bc50 = blocks["Bc"]["names_to_half_share"].get("p50")
    degs = {a: blocks[a]["names_to_half_share"].get("degenerate_share") for a in ("A", "B", "Bc")}
    return {
        "Q1": dict(claim="A' p50 of names_to_half_share is below 10%; point estimate 2-6%",
                   value=p50, held=(None if p50 is None else bool(p50 < H4_NAMES_TO_HALF_SHARE)),
                   point_estimate_held=(None if p50 is None else bool(0.02 <= p50 <= 0.06))),
        "Q2": dict(claim="the observed share is at or above A' p05 -- not unusually concentrated for its own name set",
                   value=obs["names_to_half_share"], p05=p05,
                   held=(None if p05 is None else bool(obs["names_to_half_share"] >= p05))),
        "Q3": dict(claim="A' p50 of top1_name_share is between 4% and 12%", value=t1,
                   held=(None if t1 is None else bool(0.04 <= t1 <= 0.12))),
        "Q4": dict(claim="degenerate draws under 5% for A' and B_c, and higher for B than either", values=degs,
                   held=(None if any(v is None for v in degs.values()) else
                         bool(degs["A"] < 0.05 and degs["Bc"] < 0.05 and degs["B"] > max(degs["A"], degs["Bc"])))),
        "Q5": dict(claim="AGAINST myself: [MONO] finds no discrepancy -- D373's 18 of 796 stands",
                   held=bool(mono["agrees"] and mono["d373_correct"]), detail=mono),
        "Q6": dict(claim="B_c p50 within 2 percentage points of A' p50 -- concentration is the return distribution, not selection",
                   values=dict(A=p50, Bc=bc50),
                   held=(None if (p50 is None or bc50 is None) else bool(abs(bc50 - p50) <= 0.02))),
    }


def print_report(out):
    o = out["observed"]
    print(f"\n  {out['cell']}  {o['trades']:,} trades, {o['n_names']} names")
    print(f"  observed names_to_half {o['names_to_half']} of {o['n_names']} = {o['names_to_half_share']:.4%}   "
          f"top1 {o['top1_name_share']:.4%}  top5 {o['top5_name_share']:.4%}")
    print(f"  draws: {out['controls']['draws']}   floor: {out['controls']['floor']}")
    m = out["mono"]
    print(f"  [MONO] scan {m['scan']} vs searchsorted {m['searchsorted']} vs D373 published {m['d373_published']} -> "
          f"{'AGREE' if m['agrees'] else '*** DISAGREE -- D373 corrected ***'}")
    if out["refusals"]:
        print(f"  [DEG] {out['refusals']}")
    print("\n  NULL DISTRIBUTIONS  (names_to_half_share is judged on the LOW tail -- p05)")
    for a in ("A", "B", "Bc"):
        b = out["nulls"][a]["names_to_half_share"]
        if not b.get("n"):
            print(f"    {a:<3} no defined draws")
            continue
        print(f"    {a:<3} n {b['n']:>5,}  p05 {b['p05']:.4%} (SE {b['se_p05']:.4%})  p50 {b['p50']:.4%} (SE {b['se_p50']:.4%})  "
              f"p95 {b['p95']:.4%}  degenerate {b['degenerate']:,}/{b['n_draws']:,}")
    print("\n  TOP-NAME SHARES, A' (judged on the HIGH tail -- p95)")
    for st in ("top1_name_share", "top5_name_share", "top10_name_share"):
        b = out["nulls"]["A"][st]
        if b.get("n"):
            print(f"    {st:<20} obs {out['observed'][st]:.4%}   p50 {b['p50']:.4%}  p95 {b['p95']:.4%} (SE {b['se_p95']:.4%})")
    print("\n  DECISIONS")
    print(f"    K1  {out['K1']['verdict']}")
    print(f"         A' p50 {out['K1']['p50']:.4%} vs bar {out['K1']['bar']:.0%};  B {out['K1']['other_arms']['B']}  B_c {out['K1']['other_arms']['Bc']}")
    print(f"    K2  {out['K2']['verdict']}")
    print(f"         observed {out['K2']['observed']:.4%} vs A' p05 {out['K2']['p05']:.4%}")
    for st, d in out["K3"].items():
        print(f"    K3  {st:<20} obs {d['observed']:.4%}  bar {d['bar']:.0%}  A' p95 {d['p95']:.4%}  "
              f"-> bar failable by a random book: {d['bar_failable']}")
    print(f"    K4  replacement applies: {out['K4']['applies']}   thresholds {out['K4']['thresholds_for_this_ledger']}")
    print("\n  PREDICTIONS")
    for k, v in out["predictions"].items():
        print(f"    {k}  {'HELD' if v['held'] else ('FALSIFIED' if v['held'] is not None else 'UNRESOLVED')}   {v['claim']}")


# ------------------------------------------------------------------ [X] the self-test that must RAISE
def stage_selftest(P):
    print("\nSELFTEST")
    t0 = time.time()
    res = observed_book(P)

    print("  [MIR] the inherited cell reproduces D373's committed ledger")
    mir = assert_MIR(P, res)
    print(f"       {mir['trades']:,} trades  mean {mir['mean_bp']:+.2f}  median {mir['median_bp']:+.2f}")

    print("  [CAL] the concentration function reproduces D373's four_groups")
    cs = conc_of(res, P)
    assert_CAL(cs)

    print("  [MONO] linear scan vs searchsorted on the observed book")
    mono = assert_MONO(cs)
    print(f"       scan {mono['scan']}  searchsorted {mono['searchsorted']}  published {mono['d373_published']}  "
          f"{'AGREE' if mono['agrees'] else '*** DISAGREE ***'}")

    print("  [DIR] concentration is the LOW tail")
    d = assert_DIR(P)
    print(f"       one-name {d['one_name']:.4f} < uniform {d['uniform']:.4f}")

    print("  [L][S][E] D373's inherited audits still fire")
    V73.stage_selftest(P)

    print("\n  [X] the audits RAISE on a deliberately broken book")
    broken = {}

    def must_raise(name, fn):
        try:
            fn()
        except AssertionError:
            broken[name] = "RAISED"
            return
        broken[name] = "*** DID NOT RAISE ***"
        raise AssertionError(f"[X] {name} did not raise -- a self-test that cannot fail is worse than none")

    must_raise("mir_wrong_ledger", lambda: assert_MIR(P, dict(trades=res["trades"][:10], **{k: v for k, v in res.items() if k != "trades"})))
    must_raise("cal_shifted_shares", lambda: assert_CAL({**cs, "top1_name_share": cs["top1_name_share"] + 1e-6}))
    must_raise("cal_wrong_n_names", lambda: assert_CAL({**cs, "n_names": cs["n_names"] + 1}))
    must_raise("mono_impossible_scan", lambda: assert_MONO({**cs, "names_to_half": cs["n_names"] + 1}))

    # [DIR] must reject an INVERTED statistic: a concentration measure that ranks the one-name book above the uniform one.
    def inverted_dir():
        c = conc_stats(*synth_book(P, "onename"), P)
        u = conc_stats(*synth_book(P, "uniform"), P)
        assert (1 - c["names_to_half_share"]) < (1 - u["names_to_half_share"]), "[DIR] inverted"
    must_raise("dir_inverted_statistic", inverted_dir)
    for k, v in broken.items():
        print(f"       {k}: {v}")

    print("\n  [DEG] the degenerate guard refuses rather than reporting")
    bad = pct_block([None] * 30 + [0.05] * 70)
    r = assert_DEG(bad, "test")
    assert r and "REFUSED" in r, f"[DEG] a 30% degenerate arm was not refused: {r!r}"
    print(f"       {r}")
    ok = pct_block([None] * 5 + [0.05] * 95)
    assert assert_DEG(ok, "test") is None, "[DEG] a 5% degenerate arm was wrongly refused"
    print(f"       5% degenerate: reported, {ok['degenerate']}/{ok['n_draws']} excluded from the percentiles")

    print(f"\n  selftest OK ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--observed", action="store_true")
    ap.add_argument("--cells", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--draws", type=int, default=400)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--out-dir", default=str(DATA))
    a = ap.parse_args()
    print("D374  is the breadth hurdle reachable? H4's names-to-half bar, calibrated against its own nulls")
    paths = out_paths(a.out_dir)
    P = prep()
    if a.selftest:
        stage_selftest(P)
    elif a.observed:
        stage_observed(P, paths)
    elif a.cells:
        stage_cells(P, a.draws, a.part, paths)
    elif a.report:
        stage_report(P, paths)
    else:
        ap.error("one of --selftest, --observed, --cells, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
