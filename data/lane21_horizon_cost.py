"""Lane 21 - the horizon-versus-cost arithmetic for order-book imbalance on ES.

Every number quoted in 21-order-flow-microstructure.md must reproduce from here.
Lane 14's NEW TELL 13 is "arithmetic that does not reproduce from the page's own
stated inputs"; this script is the guard against committing that tell.

MEASURED INPUTS, all from named primary sources:
  ES tick             0.25 index pts = $12.50   (CME contract spec, restated in
                                                 arXiv 2508.06788 fn.3)
  ES contract         $50 x index                (same)
  ES spread           mean 0.25, sd 0.01; the 1st through 75th percentile of the
                      one-second average spread are ALL 0.25
                                                 (arXiv 2508.06788 Table 1)
  ES 1-sec mid return mean 0.00 bp, SD 0.91 bp; p25 = p50 = p75 = 0.00 bp
                      N = 34,512,298 one-second samples, 1,490 days, 2008-2013
                                                 (arXiv 2508.06788 Table 1)
  ES top-of-book depth mean 630 contracts, median 550
                                                 (arXiv 2508.06788 Table 1)
  horizon             "shocks dissipate almost entirely within a second"
                                                 (arXiv 2508.06788 abstract)
  R2_OS of OFI        ~1% typical, ~5% best large-tick, at horizons of 0-2
                      average price changes, 115 Nasdaq stocks 2019-2020
                                                 (Kolm/Turiel/Westray 2023)
"""
import math

TICK_PTS, TICK_USD, MULT = 0.25, 12.50, 50.0
MES_TICK_USD = 1.25
SPREAD_RT = TICK_USD          # taker pays half a tick each way vs mid = 1 tick
COMM = {"retail $4.00/RT": 4.00, "screen convention $10.00/RT": 10.00}

SD_1S_BP = 0.91               # arXiv 2508.06788 Table 1, mid-quote return SD
P_SAMPLE = 1250.0             # approx S&P 500 level over the paper's 2008-2013
P_TODAY = 6700.0              # approx level, 2026

R2 = {"typical R2_OS 1%": 0.010, "best large-tick R2_OS 5%": 0.050}
SIGNAL_SD = [1.0, 2.0, 3.0]   # how extreme the imbalance reading is


def tick_in_bp(p):
    return 1e4 * TICK_PTS / p


def bp_to_usd(bp, p):
    return 1e-4 * bp * MULT * p


print("=" * 76)
print("0. IS ES A LARGE-TICK BOOK?  (the load-bearing premise)")
print("=" * 76)
print("arXiv 2508.06788 Table 1: average spread p1..p75 = 0.25, p95 = 0.26,")
print("p99 = 0.30, mean 0.25 sd 0.01.  The ES spread IS one tick, essentially")
print("always. So the mid moves on queue depletion, in half-tick increments,")
print("and a taker's round turn costs one FULL tick against the mid.")
print()

print("=" * 76)
print("1. THE ONE-SECOND MOVE, IN TICKS AND DOLLARS")
print("=" * 76)
for label, p in [("paper's era, index ~%.0f" % P_SAMPLE, P_SAMPLE),
                 ("today, index ~%.0f" % P_TODAY, P_TODAY)]:
    t_bp = tick_in_bp(p)
    sd_usd = bp_to_usd(SD_1S_BP, p)
    print("%-28s 1 tick = %5.3f bp | 1-sec SD %.2f bp = %5.2f ticks = $%6.2f"
          % (label, t_bp, SD_1S_BP, SD_1S_BP / t_bp, sd_usd))
print()
print("NOTE: holding SD_1S_BP fixed across eras assumes similar RELATIVE vol.")
print("The 2008-2013 sample spans the GFC, so its 0.91bp is a HIGH-vol read;")
print("carrying it to today therefore FAVOURS the strategy. Both are shown.")
print()
print("And the median one-second ES mid move is EXACTLY ZERO:")
print("  Table 1 percentiles 25%/50%/75% of the 1-sec mid return = 0.00 bp.")
print("  A majority of seconds contain no mid-price move to predict at all.")
print()

print("=" * 76)
print("2. E[gross move | imbalance signal] vs THE ROUND TURN")
print("=" * 76)
print("E[r | s] = rho * sigma * s, with rho = sqrt(R2_OS).")
print("R2 is imported from Nasdaq EQUITIES (Kolm et al.); no published ES")
print("equivalent exists. ES is large-tick/deep-queue/high-update, which is")
print("exactly the profile where Kolm finds the BEST R2 -- so the transfer")
print("is GENEROUS to the strategy, and the conclusion survives it anyway.")
print()
for p_label, p in [("2008-2013", P_SAMPLE), ("today", P_TODAY)]:
    sd_usd = bp_to_usd(SD_1S_BP, p)
    print("-- index %s (sigma_1s = $%.2f) --" % (p_label, sd_usd))
    print("%-26s %-8s %10s %10s %10s" % ("R2", "signal", "E[gross]$",
                                         "cost$(4)", "shortfall"))
    for rl, r2 in R2.items():
        rho = math.sqrt(r2)
        for s in SIGNAL_SD:
            eg = rho * sd_usd * s
            c4 = SPREAD_RT + COMM["retail $4.00/RT"]
            print("%-26s %-8s %10.2f %10.2f %9.1fx"
                  % (rl, "%.0f sd" % s, eg, c4, c4 / eg))
    print()

print("=" * 76)
print("2b. THE ONE CELL THAT CLEARS, STRESSED")
print("=" * 76)
print("Only R2=5% x 3sd x today's index clears ($20.45 vs $16.50). It stacks")
print("five favourable choices. Two are checkable:")
print()
print("(i) VOLATILITY. 0.91 bp/sec is a 2008-2013 read spanning the GFC.")
print("    Implied annualised vol = sd * sqrt(seconds per RTH year):")
SEC_YR = 252 * 6.5 * 3600
for bp in (0.91, 0.75, 0.62):
    ann = 1e-4 * bp * math.sqrt(SEC_YR)
    sd_usd = bp_to_usd(bp, P_TODAY)
    eg = math.sqrt(0.05) * sd_usd * 3.0
    c = SPREAD_RT + 4.00
    print("    %.2f bp/sec -> %.0f%% ann. vol | sigma_1s $%5.2f | best-cell "
          "E[gross] $%5.2f vs cost $%.2f -> %s"
          % (bp, 100 * ann, sd_usd, eg, c, "CLEARS" if eg > c else "FAILS"))
print("    At anything below ~0.85 bp/sec -- i.e. below ~21%% annualised --")
print("    the last surviving cell fails too.")
print()
print("(ii) LINEAR EXTRAPOLATION TO 3sd. E[r|s] = rho*sigma*s is linear and")
print("     OVERSTATES at the extreme: Gould-Bonart's fitted relation")
print("     SATURATES at P(up) ~ 0.8-0.9. Section 5 uses that measured")
print("     conditional probability instead of extrapolating, and at the")
print("     one-second horizon it loses in every cell. Where the two methods")
print("     disagree, the saturating one is the correct one.")
print()

print("=" * 76)
print("3. REQUIRED HIT RATE, TAKER, over 1-3 mid-price changes")
print("=" * 76)
print("E = gross*(2p-1) - cost = 0  ->  p_req = 0.5 + cost/(2*gross)")
print("granularity: the mid moves in HALF ticks on a pinned book; a FULL tick")
print("per mid-price change is carried as the generous alternative.")
print()
for cname, comm in COMM.items():
    cost = SPREAD_RT + comm
    print("-- %s : round-turn cost vs mid = $%.2f = %.2f ES ticks --"
          % (cname, cost, cost / TICK_USD))
    print("%-24s %-8s %9s %9s %9s" % ("granularity", "horizon", "gross$",
                                      "cost$", "p_req"))
    for gname, g in [("half-tick moves", 0.5), ("full-tick (generous)", 1.0)]:
        for h in (1, 2, 3):
            gross = h * g * TICK_USD
            p = 0.5 + cost / (2.0 * gross)
            flag = "  IMPOSSIBLE (>1)" if p > 1.0 else ""
            print("%-24s %-8s %9.2f %9.2f %9.3f%s"
                  % (gname, "%d chg" % h, gross, cost, p, flag))
    print()

print("=" * 76)
print("4. THE HIT RATE THE LITERATURE ACTUALLY DOCUMENTS")
print("=" * 76)
for rl, r2 in R2.items():
    acc = 0.5 + math.asin(math.sqrt(r2)) / math.pi   # Gaussian orthant map
    print("%-28s -> directional accuracy %.3f" % (rl, acc))
print("Gould-Bonart 2016 out-of-sample AUC, large-tick: 0.752 - 0.805")
print("  (AUC is not a hit rate. Their local-logistic P(up) at EXTREME")
print("   imbalance is 'about 0.8 to 0.9' -- the practitioner's best case.)")
print()

print("=" * 76)
print("5. BEST CASE: p = 0.85 SUSTAINED over the whole horizon")
print("=" * 76)
for gname, g in [("half-tick moves", 0.5), ("full-tick (generous)", 1.0)]:
    for h in (1, 2, 3):
        gross = h * g * TICK_USD
        row = "%-22s h=%d gross $%6.2f |" % (gname, h, gross)
        for cname, comm in COMM.items():
            ev = gross * (2 * 0.85 - 1) - (SPREAD_RT + comm)
            row += "  EV $%+7.2f (%s)" % (ev, cname.split()[0])
        print(row)
print()
best = 3 * 1.0 * TICK_USD * 0.70 - (SPREAD_RT + 4.00)
print("only surviving cells need FULL-tick moves AND h>=2 AND retail $4.")
print("best cell EV = $%.2f/RT  ->  %.1f round turns/day for $150,"
      % (best, 150.0 / best))
print("each needing a fresh 85%-accurate 3-price-change forecast, at a")
print("horizon the same literature says is dead after 2-3 price changes.")
print()

print("=" * 76)
print("6. MICROS ARE WORSE, NOT SAFER")
print("=" * 76)
print("ES : spread $%.2f + $4.00 = $%.2f = %.2f ES ticks"
      % (TICK_USD, TICK_USD + 4, (TICK_USD + 4) / TICK_USD))
for mc in (1.00, 1.50):
    print("MES: spread $%.2f + $%.2f = $%.2f = %.2f MES ticks"
          % (MES_TICK_USD, mc, MES_TICK_USD + mc, (MES_TICK_USD + mc) / MES_TICK_USD))
print("Commission is a LARGER fraction of the micro tick, so sizing down")
print("into MES raises the cost hurdle by %.0f-%.0f%%."
      % (100 * ((MES_TICK_USD + 1.0) / MES_TICK_USD) / ((TICK_USD + 4) / TICK_USD) - 100,
         100 * ((MES_TICK_USD + 1.5) / MES_TICK_USD) / ((TICK_USD + 4) / TICK_USD) - 100))
