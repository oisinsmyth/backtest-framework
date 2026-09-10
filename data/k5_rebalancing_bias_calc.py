import math

def bias_enum(s):
    """Exhaustive 4-state enumeration of Blume-Stambaugh's bid-ask bounce setup.
    True price (midpoint) = 1, constant. Observed price is ask A=1+s/2 or bid B=1-s/2,
    iid fair coin each period. s = (A-B)/midpoint = relative spread."""
    A = 1 + s / 2
    B = 1 - s / 2
    rets = [p1 / p0 - 1 for p0 in (A, B) for p1 in (A, B)]
    return sum(rets) / 4

print("--- verify closed form  E[R_obs] = s^2/(4-s^2)  against enumeration ---")
for s in [0.10, 0.0676, 0.0323, 0.01]:
    print("s=%.4f  enumerated=%.8f  closed_form=%.8f  sigma2=s^2/4=%.8f"
          % (s, bias_enum(s), s * s / (4 - s * s), s * s / 4))

print()
print("--- programme's own held-name spread: 33.8 bp/side ---")
s = 2 * 0.00338
b = s * s / (4 - s * s)
print("round-trip relative spread s = %.1f bp ; per-rebalance bias = %.4f bp" % (s * 1e4, b * 1e4))
for H in [1, 2, 5, 10, 20, 40]:
    per_bar = b / H
    ann = (1 + per_bar) ** 252 - 1
    print("  hold H=%3d bars: per-bar %.4f bp -> annualised %.3f %%/yr" % (H, per_bar * 1e4, ann * 100))

print()
print("--- invert: what spread does each published/measured annual figure imply at DAILY re-equalisation? ---")
for tgt, label in [(1.0679, "microcap decile +6.79%/yr"),
                   (1.0030, "above-floor deciles, low end +0.30%/yr"),
                   (1.0128, "above-floor deciles, high end +1.28%/yr"),
                   (1.0604, "Canina et al. CRSP EW +6.04%/yr")]:
    x = math.exp(math.log(tgt) / 252) - 1
    s_imp = math.sqrt(4 * x / (1 + x))
    print("%-40s per-bar %.4f bp ; implied s = %.1f bp round trip = %.1f bp/side"
          % (label, x * 1e4, s_imp * 1e4, s_imp * 1e4 / 2))

print()
print("--- ABK Prop.1 calibration check: sigma=0.06 monthly (Brennan-Wang) ---")
sig = 0.06
mu = 1.01
for rho in [0.0, 0.25, 0.5]:
    bias_m = mu * sig * sig * (1 - rho)
    print("rho=%.2f : EW monthly bias = %.4f = %.1f bp/month -> %.2f %%/yr at monthly rebalancing"
          % (rho, bias_m, bias_m * 1e4, ((1 + bias_m) ** 12 - 1) * 100))
