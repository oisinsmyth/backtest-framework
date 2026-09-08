"""D393 -- is `up_run_21` a NEW effect, or `rev_21` reversal at lower fidelity?

    uv run python scripts/run_d393_bs_null.py --selftest
    uv run python scripts/run_d393_bs_null.py --overlap        # minutes, no nulls
    uv run python scripts/run_d393_bs_null.py --calibrate      # time B_s, project, then decide
    uv run python scripts/run_d393_bs_null.py --bs             # the null

THE QUESTION, from D393-ADDENDUM section 2. `up_run_21` earns +22.06 bp/trade and `up_frac_21`
earns +21.62 on ~21,000 trades each. `up_frac_21` is not a candidate -- K1 killed it at rho +0.601
to `rev_21` as "the 21-day return with the magnitude removed". `up_run_21` survived K1 only because
rho +0.370 sits under a 0.5 bar. **The parsimonious reading is that both are the reversal effect
FINDINGS section 31 already prices at +38 bp**, and the addendum could not distinguish them.

TWO MEASUREMENTS, in increasing cost, authorised by the principal 2026-09-08.

  --overlap  Set algebra, no nulls. How much of `up_run_21`'s book IS `rev_21`'s book? Held
             name-bars (the D365/D373 statistic, which found 70.1%), trade keys, and -- the one
             that actually decides it -- **what `up_run_21` earns on the trades `rev_21`'s own E1
             does NOT take.** If the disjoint part earns nothing, the score is a proxy.

  --bs       B_s: each event's name replaced by a random eligible name in the SAME `rev_21` DECILE
             that day. Declared LOAD-BEARING in the pre-registration section 4 for exactly this
             failure mode: if the sign statistic is a trailing-return proxy, this null holds the
             trailing return fixed and the candidate has nothing left.

**`up_frac_21` IS RUN AS THE NULL'S OWN POSITIVE CONTROL, and that is not optional.** It is the
score K1 killed as a `rev_21` proxy. **A B_s that fails to kill it is a broken null**, and its
verdict on `up_run_21` would prove nothing. This is CLAUDE.md's "a self-test that cannot fail is
worse than none" applied to a null rather than to an assertion.

B_s DIFFERS FROM D359's B_c AND THE DIFFERENCE MATTERS. `run_d359.control_bc_signal` draws from ONE
cohort mask shared by every event that day. B_s must draw from **each event's OWN decile** -- two
events on the same bar in different `rev_21` deciles have different pools. The deciles partition
the eligible set, so the per-decile pools are disjoint and the daily draw stays collision-free.

SCOPE. One cell -- E1, cap 20, long -- not the 10-cell grid of section 4. That narrowing is the
principal's, given 2026-09-08. **No holdout read; the holdout is a disjoint SYMBOL set in its own
fixture. No null but B_s. Nothing here admits anything (R15).**
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
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


OVL_OUT = REPO / "data" / "d393_overlap.json"
BS_OUT = REPO / "data" / "d393_bs_null.json"
AP_OUT = REPO / "data" / "d393_aprime_null.json"
NPZ = REPO / "temp" / "d290_scores.npz"

CAP = 20
CANDIDATE = "up_run_21"
CONTROL = "up_frac_21"                # K1 killed it; the NULL's positive control
REF = "rev_21"                        # the effect both are suspected of being
SEED = 393
N_DRAWS = 2000                        # section 4's count, on one cell rather than ten
NSHARDS = 8


def SHARD(i, kind="Bs"):
    return REPO / "temp" / f"d393_{kind}_shard_{i}.json"


def item_at(idx, n_draws):
    """The (score, seed) of draw `idx`, and THE ONLY definition of it.

    The serial list is [CANDIDATE] * n_draws then [CONTROL] * n_draws, each with seed SEED+1+i.
    Every path -- serial, threaded, sharded -- reads the draw list through here, so a shard cannot
    silently disagree with the whole about which draw an index names."""
    if idx < n_draws:
        return CANDIDATE, SEED + 1 + idx
    return CONTROL, SEED + 1 + (idx - n_draws)


def merge_shards(n_draws, nshards, kind="Bs"):
    """Reassemble the strided shards, ASSERTING full coverage before anything is scored."""
    got = {}
    for i in range(nshards):
        p = SHARD(i, kind)
        assert p.exists(), f"shard {i} missing: {p}"
        d = json.loads(p.read_text())
        assert d["n_draws"] == n_draws and d["nshards"] == nshards, f"shard {i} ran a different fan"
        for k, v in d["values"].items():
            k = int(k)
            assert k not in got, f"index {k} appears in two shards"
            got[k] = v
    missing = set(range(2 * n_draws)) - set(got)
    assert not missing, f"{len(missing)} draws missing, e.g. {sorted(missing)[:5]}"
    out = {CANDIDATE: [], CONTROL: []}
    for i in range(2 * n_draws):
        out[item_at(i, n_draws)[0]].append(got[i])
    assert len(out[CANDIDATE]) == len(out[CONTROL]) == n_draws
    return out


# ------------------------------------------------------------------ B_s
def control_bs_signal(mask, dec, elig, rng):
    """B_s: each event (t, i) -> a random eligible name in the SAME `rev_21` decile that day,
    distinct within (day, decile), never an event name. Short pools keep their name and are
    counted, which is D359's B_c convention.

    `dec` is the decile index 0..9, or -1 where `rev_21` is not finite -- those events swap within
    the not-finite group rather than being dropped, so the event COUNT is preserved exactly."""
    out = np.zeros_like(mask)
    kept = 0
    for t in np.flatnonzero(mask.any(axis=1)):
        ev = np.flatnonzero(mask[t])
        for d in np.unique(dec[t, ev]):
            evd = ev[dec[t, ev] == d]
            pool = np.flatnonzero(elig[t] & (dec[t] == d) & ~mask[t])
            k = min(evd.size, pool.size)
            if k:
                out[t, rng.choice(pool, size=k, replace=False)] = True
            if evd.size > k:
                out[t, evd[k:]] = True
                kept += evd.size - k
    return out, kept


def assert_Bs(sig, mask, dec, elig, kept):
    """[Bs] dates kept, count kept, every replacement eligible and in the right decile, and the
    shortfall recounted independently -- D359's assert_Bc, per-decile."""
    assert np.array_equal(sig.sum(axis=1), mask.sum(axis=1)), "[Bs] dates changed"
    rep = sig & ~mask
    assert not (rep & ~elig).any(), "[Bs] a replacement is ineligible"
    assert int((sig & mask).sum()) == kept, "[Bs] kept != counted shortfall"
    short = 0
    for t in np.flatnonzero(mask.any(axis=1)):
        ev = np.flatnonzero(mask[t])
        for d in np.unique(dec[t, ev]):
            evd = ev[dec[t, ev] == d]
            pool = int((elig[t] & (dec[t] == d) & ~mask[t]).sum())
            short += max(0, evd.size - pool)
            # every replacement placed in this decile came FROM this decile
            got = np.flatnonzero(rep[t] & (dec[t] == d))
            assert got.size <= evd.size, f"[Bs] decile {d} over-filled on bar {t}"
    assert short == kept, f"[Bs] shortfall recount {short} != kept {kept}"
    return int(rep.sum())


# ------------------------------------------------------------------ shared prep
def build(PREP, V50, SG):
    P = PREP.prep(need_grids=True)
    M = PREP.M
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    live = panel.live
    T, n = P["T"], P["n"]
    elig = np.asarray(P["elig"])

    def lagged_from(arr):
        sc = np.where(P["excl"], np.nan, arr)
        sc = PREP.UF.apply_floor_replace(sc, P["keep"])
        sc = np.where(P["base"], sc, np.nan)
        out = np.full((T, n), np.nan)
        out[1:] = sc[:, :-1].T
        return out

    raw = SG.sign_scores(g, live)
    cols = {k: lagged_from(raw[k]) for k in (CANDIDATE, CONTROL)}
    cols[REF] = lagged_from(np.asarray(P["score"](REF)))
    pct = {k: PREP.V47.percentile_grid(v) for k, v in cols.items()}
    masks = {k: V50.shape_masks(pct[k], elig)["E1"][0] for k in cols}
    # the rev_21 decile, LAGGED like everything else; -1 where it is not defined
    dec = np.full(pct[REF].shape, -1, np.int8)
    fin = np.isfinite(pct[REF])
    dec[fin] = np.clip((pct[REF][fin] // 10.0).astype(np.int8), 0, 9)
    return P, elig, cols, masks, dec, T, n


def held_grid(res, T, n):
    """The name-bars a ledger actually holds, from its trades: [entry, entry+held)."""
    h = np.zeros((T, n), bool)
    for tr in res["trades"]:
        i, t0, age = tr[0], tr[1], tr[2]
        h[t0:min(t0 + age, T), i] = True
    return h


def jac(a, b):
    u = int((a | b).sum())
    return float((a & b).sum()) / u if u else float("nan")


# ------------------------------------------------------------------ the overlap check
def overlap(PREP, V50, SG, V59) -> int:
    t0 = time.time()
    P, elig, cols, masks, dec, T, n = build(PREP, V50, SG)
    print(f"  prep + scores in {time.time() - t0:.0f}s", flush=True)

    res, pnl, held, keys = {}, {}, {}, {}
    for k in (CANDIDATE, CONTROL, REF):
        sc = np.where(np.isfinite(cols[k]), cols[k], 50.0)
        res[k] = V59.run_mirror(P, masks[k], sc, "cap", CAP)
        pnl[k] = PREP.V47.pnl_bp(res[k])
        held[k] = held_grid(res[k], T, n)
        keys[k] = {(tr[0], tr[1]) for tr in res[k]["trades"]}
        print(f"    {k:<14s} {len(res[k]['trades']):>7,} trades, gross "
              f"{pnl[k].mean():+7.2f} bp", flush=True)

    ov = {}
    for a, b in ((CANDIDATE, REF), (CANDIDATE, CONTROL), (CONTROL, REF)):
        ov[f"{a}|{b}"] = dict(
            events_jaccard=jac(masks[a], masks[b]),
            held_namebars_jaccard=jac(held[a], held[b]),
            held_share_of_a=float((held[a] & held[b]).sum()) / max(1, int(held[a].sum())),
            trades_shared=len(keys[a] & keys[b]),
            trade_share_of_a=len(keys[a] & keys[b]) / max(1, len(keys[a])))

    # ---- THE DECIDING SPLIT: what does the candidate earn OFF the reference's book? -------
    tr_c = res[CANDIDATE]["trades"]
    shared = np.array([(tr[0], tr[1]) in keys[REF] for tr in tr_c])
    p = pnl[CANDIDATE]
    split = {
        "shared_with_rev21_E1": dict(n=int(shared.sum()),
                                     mean_bp=float(p[shared].mean()) if shared.any() else None,
                                     median_bp=float(np.median(p[shared])) if shared.any() else None),
        "DISJOINT_from_rev21_E1": dict(n=int((~shared).sum()),
                                       mean_bp=float(p[~shared].mean()) if (~shared).any() else None,
                                       median_bp=float(np.median(p[~shared])) if (~shared).any() else None)}

    payload = dict(study=393, stage="overlap", cap=CAP, shape="E1", side="long",
                   purpose="Is up_run_21 rev_21's E1 book wearing a new label? Set algebra plus "
                           "the candidate's mean off the reference's book. No null. Admits "
                           "nothing (R15).",
                   trades={k: len(res[k]["trades"]) for k in res},
                   gross_bp={k: float(pnl[k].mean()) for k in pnl},
                   overlap=ov, candidate_split=split,
                   caveat="candidate_split is a DIAGNOSTIC conditional split, not a candidate "
                          "cell and not pre-registered.")
    OVL_OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  [P] wrote {OVL_OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    print("\nOVERLAP -- how much of one book IS the other\n")
    print(f"  {'pair':<32s} {'events J':>9s} {'heldbar J':>10s} {'held/a':>8s} "
          f"{'trades':>8s} {'trades/a':>9s}")
    for k, d in ov.items():
        print(f"  {k:<32s} {d['events_jaccard']:9.3f} {d['held_namebars_jaccard']:10.3f} "
              f"{d['held_share_of_a']:8.3f} {d['trades_shared']:8,} {d['trade_share_of_a']:9.3f}")
    print(f"\nTHE DECIDING SPLIT -- {CANDIDATE}'s trades, by whether {REF}'s OWN E1 takes them\n")
    for nm, d in split.items():
        print(f"  {nm:<26s} n {d['n']:>7,}  mean {d['mean_bp']:+8.2f} bp  "
              f"median {d['median_bp']:+8.2f}")
    print(f"\n  ({time.time() - t0:.0f}s)  No null was run.")
    return 0


# ------------------------------------------------------------------ the B_s null
def bs(PREP, V50, SG, V59, FN, n_draws, calibrate,
       shard=None, nshards=NSHARDS, verify_shard=False, null_kind="Bs", V73=None) -> int:
    t0 = time.time()
    P, elig, cols, masks, dec, T, n = build(PREP, V50, SG)
    print(f"  prep + scores in {time.time() - t0:.0f}s", flush=True)

    obs = {}
    for k in (CANDIDATE, CONTROL):
        sc = np.where(np.isfinite(cols[k]), cols[k], 50.0)
        r = V59.run_mirror(P, masks[k], sc, "cap", CAP)
        obs[k] = float(PREP.V47.pnl_bp(r).mean())
    print(f"  observed: {CANDIDATE} {obs[CANDIDATE]:+.2f} | {CONTROL} "
          f"{obs[CONTROL]:+.2f} (the null's positive control)", flush=True)

    # ---- the null's own assertions on one draw, and the negative control ---
    rng0 = np.random.default_rng(SEED)
    if null_kind == "Bs":
        sig0, kept0 = control_bs_signal(masks[CANDIDATE], dec, elig, rng0)
        nrep = assert_Bs(sig0, masks[CANDIDATE], dec, elig, kept0)
        bad = sig0.copy()
        j = np.flatnonzero(bad.any(axis=1))[0]
        bad[j, np.flatnonzero(~elig[j])[0]] = True      # an ineligible replacement
        try:
            assert_Bs(bad, masks[CANDIDATE], dec, elig, kept0)
            raise SystemExit("[X] assert_Bs did NOT fire on an ineligible replacement")
        except AssertionError:
            pass
        print(f"    [Bs] {nrep:,} replacements, {kept0:,} kept for a short pool; and the "
              f"assertion RAISES on an ineligible replacement", flush=True)
    else:
        # A' -- D373's own three assertions (no short leg, nothing off the floor, per-name count
        # preserved) fire inside aprime_draw_long. What is checked HERE is that they can fail, and
        # that the rotation actually MOVED the events rather than returning them unchanged.
        sc0 = np.where(np.isfinite(cols[CANDIDATE]), cols[CANDIDATE], 50.0)
        sig0, _sc0 = V73.aprime_draw_long(masks[CANDIDATE], sc0, elig, rng0)
        assert int(sig0.sum()) == int(masks[CANDIDATE].sum()), "[A'] total event count changed"
        assert np.array_equal(sig0.sum(axis=0), masks[CANDIDATE].sum(axis=0)), \
            "[A'] per-name event count changed"
        assert not (sig0 & ~elig).any(), "[A'] a rotated event landed off the eligible mask"
        moved = int((sig0 & ~masks[CANDIDATE]).sum())
        assert moved > 0.5 * int(masks[CANDIDATE].sum()), \
            f"[A'] only {moved} events moved -- the rotation is barely rotating"
        try:
            V73.aprime_draw_long(masks[CANDIDATE], sc0, np.zeros_like(elig), rng0)
            raise SystemExit("[X] aprime_draw_long did NOT fire on an all-ineligible mask")
        except AssertionError:
            pass
        print(f"    [A'] {moved:,} of {int(masks[CANDIDATE].sum()):,} events moved to a new bar; "
              f"per-name counts preserved, nothing off the floor; and the rotation RAISES when "
              f"handed an empty eligible mask", flush=True)

    # `parallel_map(fn, items)` calls `fn(k, v)` over (key, value) pairs and returns {key: result},
    # so the key must be unique per draw -- "<score>:<i>", not the score name.
    #
    # A' REUSES D373's `aprime_draw_long` RATHER THAN REIMPLEMENTING THE ROTATION. That function
    # carries D351's three assertions -- no short leg appears, no rotated event lands off the
    # floor, the per-name event count is preserved -- and a second copy here would be a second
    # thing to keep right. The score is rotated WITH the events, which is what makes it a timing
    # null rather than a different book.
    def one(_key, v):
        k, s = v
        rng = np.random.default_rng(s)
        if null_kind == "A":
            sc = np.where(np.isfinite(cols[k]), cols[k], 50.0)
            sig, sc_ = V73.aprime_draw_long(masks[k], sc, elig, rng)
        else:
            sig, _ = control_bs_signal(masks[k], dec, elig, rng)
            sc_ = np.full((T, n), 17.0)
        r = V59.run_mirror(P, sig, sc_, "cap", CAP)
        return float(PREP.V47.pnl_bp(r).mean())

    if calibrate:
        m = 8
        t1 = time.time()
        for i in range(m):
            one(f"cal:{i}", (CANDIDATE, SEED + i))
        per = (time.time() - t1) / m
        print(f"\n  CALIBRATION: {per:.2f} s/draw serial -> {2 * n_draws * per / 60:.0f} min "
              f"serial for {n_draws} draws x 2 scores", flush=True)
        items = [(f"t:{i}", (CANDIDATE, SEED + 10_000 + i)) for i in range(m)]
        t2 = time.time()
        FN.parallel_map(one, items, progress=None)
        wall = max(time.time() - t2, 1e-9)
        sp = m * per / wall
        print(f"  threaded on {m}: {wall:.1f}s wall vs {m * per:.1f}s serial ({sp:.2f}x) "
              f"-> projected {2 * n_draws * per / sp / 60:.0f} min", flush=True)
        return 0

    if shard is not None:
        # ---- one process's stride of the draw list -------------------------
        idxs = [i for i in range(2 * n_draws) if i % nshards == shard]
        got = {}
        for c, i in enumerate(idxs):
            k, s = item_at(i, n_draws)
            got[i] = one(f"{k}:{i}", (k, s))
            if c % 50 == 0:
                print(f"    shard {shard}: {c}/{len(idxs)} ({time.time() - t0:.0f}s)", flush=True)
        SHARD(shard, null_kind).write_text(json.dumps({"n_draws": n_draws, "nshards": nshards,
                                            "shard": shard, "values": got}))
        print(f"  shard {shard}: {len(idxs)} draws -> {SHARD(shard, null_kind).name} "
              f"({time.time() - t0:.0f}s)", flush=True)
        return 0

    if verify_shard:
        # ---- CLAUDE.md: prove chunk == whole BEFORE trusting the fan -------
        m = 12
        seq = [one(f"v:{i}", item_at(i, m // 2)) for i in range(m)]
        strided = {}
        for sh in range(4):
            for i in [j for j in range(m) if j % 4 == sh]:
                strided[i] = one(f"v:{i}", item_at(i, m // 2))
        chunk = [strided[i] for i in range(m)]
        assert seq == chunk, f"[SHARD] strided != sequential\n{seq}\n{chunk}"
        print(f"\n  [SHARD] {m} draws in 4 strides reproduce the sequential list "
              f"BIT-IDENTICALLY -- each draw is a pure function of its index", flush=True)
        return 0

    draws = merge_shards(n_draws, nshards, null_kind)

    rngb = np.random.default_rng(7)
    stats = {}
    for k in (CANDIDATE, CONTROL):
        d = np.array(draws[k])
        p95 = float(np.percentile(d, 95))
        bootp95 = np.array([np.percentile(rngb.choice(d, d.size, replace=True), 95)
                            for _ in range(400)])
        se = float(bootp95.std(ddof=1))
        margin = obs[k] - p95
        stats[k] = dict(observed=obs[k], n_draws=int(d.size), p50=float(np.median(d)),
                        p95=p95, se_p95=se, min=float(d.min()), max=float(d.max()),
                        margin=margin, within_2se=bool(abs(margin) <= 2 * se),
                        verdict=("UNRESOLVED (within 2 SE)" if abs(margin) <= 2 * se
                                 else "ABOVE" if margin > 0 else "BELOW"))

    NAME = {"Bs": "B_s", "A": "A_prime"}[null_kind]
    payload = dict(study=393, stage=NAME, cap=CAP, shape="E1", side="long", n_draws=n_draws,
                   seed=SEED,
                   purpose=("B_s on ONE cell: each event's name swapped for an eligible name "
                            "in the same rev_21 decile that day, section 4's load-bearing null."
                            if null_kind == "Bs" else
                            "A prime on ONE cell: each name's events rotated within its own "
                            "eligible bars, the score rotated with them. Tests whether the "
                            "TIMING carries the edge or the decile-crossing SHAPE does.")
                           + " Admits nothing (R15).",
                   scope_change=f"Section 4 declared {NAME} over the 10-cell grid; this runs the "
                                "PRIMARY cell only. Narrowed by the principal 2026-09-08.",
                   positive_control=f"{CONTROL} is the score K1 killed as a rev_21 proxy. If {NAME} "
                                    f"does not kill it, the null is broken and its verdict on "
                                    f"{CANDIDATE} proves nothing.",
                   stats=stats, draws={k: v for k, v in draws.items()})
    OUTP = BS_OUT if null_kind == "Bs" else AP_OUT
    OUTP.write_text(json.dumps(payload, indent=1))
    print(f"\n  [P] wrote {OUTP.relative_to(REPO)} BEFORE rendering", flush=True)

    # THE CONTROL'S EXPECTED DIRECTION IS NOT THE SAME UNDER THE TWO NULLS, and labelling it as
    # though it were is how a reader draws the wrong conclusion from a right number.
    #   B_s holds the rev_21 decile fixed. up_frac_21 IS that decile (rho +0.601), so it MUST die;
    #        a B_s that spares it has no power and its verdict on the candidate is worthless.
    #   A'  destroys TIMING and keeps the names. rev_21's own E1 timing is real and published at
    #        +38 bp (FINDINGS 31), so up_frac_21 SHOULD survive A'. Its survival is a sanity check
    #        on the null, not a failure of it.
    head = ("B_s -- swap the name inside the same rev_21 decile" if null_kind == "Bs" else
            "A' -- rotate each name's events within its own eligible bars, score rotated with them")
    print(f"\n{head}, {n_draws:,} draws, E1 cap {CAP} long\n")
    print(f"  {'score':<16s} {'obs':>8s} {'p50':>8s} {'p95':>8s} {'SE':>6s} {'margin':>8s}   verdict")
    for k in (CANDIDATE, CONTROL):
        s = stats[k]
        ctl = ("  <- CONTROL: must DIE here (it is the decile)" if null_kind == "Bs" else
               "  <- CONTROL: should SURVIVE here (rev_21 timing is real, FINDINGS 31)")
        tag = ctl if k == CONTROL else "  <- the candidate"
        print(f"  {k:<16s} {s['observed']:+8.2f} {s['p50']:+8.2f} {s['p95']:+8.2f} "
              f"{s['se_p95']:6.2f} {s['margin']:+8.2f}   {s['verdict']}{tag}")
    print(f"\n  ({time.time() - t0:.0f}s)")
    return 0


# ------------------------------------------------------------------ self-test
def selftest() -> int:
    print("D393 B_s SELF-TEST -- the per-decile swap, on hand data\n")
    elig = np.ones((3, 8), bool)
    dec = np.array([[0, 0, 0, 0, 5, 5, 5, 5]] * 3, np.int8)
    mask = np.zeros((3, 8), bool)
    mask[0, 0] = True                 # one event in decile 0
    mask[0, 4] = True                 # one event in decile 5
    rng = np.random.default_rng(0)
    sig, kept = control_bs_signal(mask, dec, elig, rng)
    assert kept == 0 and sig.sum() == 2, (kept, sig.sum())
    got = np.flatnonzero(sig[0])
    assert dec[0, got[0]] == 0 and dec[0, got[1]] == 5, f"swapped across deciles: {got}"
    assert not (sig & mask).any(), "an event name was reused"
    print("    two events in two deciles swap WITHIN their own decile, never across")

    # a decile with no room: the event must keep its name and be counted
    tight = np.zeros((1, 3), bool)
    tight[0, 0] = True
    d2 = np.array([[1, 2, 2]], np.int8)
    s2, k2 = control_bs_signal(tight, d2, np.ones((1, 3), bool), np.random.default_rng(1))
    assert k2 == 1 and s2[0, 0], f"a short pool must keep the event: kept={k2}, sig={s2}"
    print("    a decile with no other eligible name keeps the event and COUNTS it")
    assert_Bs(s2, tight, d2, np.ones((1, 3), bool), k2)
    print("    [Bs] passes on a correct draw")
    print("\nSELF-TEST PASSED")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--overlap", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--bs", action="store_true", help="merge the shards and score")
    ap.add_argument("--null", choices=("Bs", "A"), default="Bs",
                    help="Bs: same-rev_21-decile name swap. A: per-name time rotation (A prime)")
    ap.add_argument("--shard", type=int, help="run only draws where idx %% nshards == shard")
    ap.add_argument("--nshards", type=int, default=NSHARDS)
    ap.add_argument("--verify-shard", action="store_true",
                    help="prove a strided fan reproduces the sequential list bit-identically")
    ap.add_argument("--draws", type=int, default=N_DRAWS)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    selftest()
    PREP = _load("d348p", "d348_prep.py")
    SG = _load("ragged_sign_scores", "ragged_sign_scores.py")
    V50 = _load("d350r", "run_d350_long_timing_screen.py")
    V59 = _load("d359r", "run_d359_loser_rally_short.py")
    if a.overlap:
        return overlap(PREP, V50, SG, V59)
    if a.calibrate or a.bs or a.shard is not None or a.verify_shard:
        FN = _load("fast_null", "fast_null.py")
        V73 = _load("d373r", "run_d373_winners_dip_long.py") if a.null == "A" else None
        return bs(PREP, V50, SG, V59, FN, a.draws, a.calibrate,
                  shard=a.shard, nshards=a.nshards, verify_shard=a.verify_shard,
                  null_kind=a.null, V73=V73)
    ap.error("pass --overlap, --calibrate, --shard, --verify-shard or --bs")


if __name__ == "__main__":
    raise SystemExit(main())
