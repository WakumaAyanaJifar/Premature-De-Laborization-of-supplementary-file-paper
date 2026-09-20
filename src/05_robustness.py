"""
Robustness analyses required by the revision.

  A. Bundle sensitivity: five ex ante definitions of the digital service pathway
  B. Inference: cluster bootstrap and exact-style permutation test
  C. Age-of-entry sensitivity for the absorption arithmetic
  D. Distributional statistics within bundles
"""

import os
import numpy as np
import pandas as pd
import pyreadr

DATA, OUT = "data", "results"
rng = np.random.default_rng(20260921)

occ = pd.read_csv(os.path.join(DATA, "occ_level.csv")).rename(
    columns={"O*NET-SOC Code": "onetsoc", "Title": "title"})
occ["beta"] = occ["dv_rating_beta"]
occ["beta_h"] = occ["human_rating_beta"]
occ["soc_major"] = occ.onetsoc.str[:2]
occ["soc_minor"] = occ.onetsoc.str[:5]

BASE_MAJORS = {"31", "33", "35", "37", "39", "41", "45", "47", "49", "51", "53"}
occ["base"] = occ.soc_major.isin(BASE_MAJORS)

lines = []
def w(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    lines.append(s)


# ---------------------------------------------------------------------------
# A. Bundle sensitivity
# ---------------------------------------------------------------------------
# Occupations inside SOC 43 that no national digital economy strategy targets:
# physical mail handling, courier work, cash handling and machine operation.
NON_OFFSHORABLE_43 = {
    "43-5011.00", "43-5011.01", "43-5021.00", "43-5031.00", "43-5032.00",
    "43-5041.00", "43-5051.00", "43-5052.00", "43-5053.00", "43-5061.00",
    "43-5071.00", "43-5111.00", "43-3041.00", "43-9071.00", "43-9051.00",
}

# A narrow, literal reading of what BPO and platform freelancing contracts cover.
CORE_BPO = (
    "15-1251", "15-1252", "15-1254", "15-1253", "15-1232", "15-1231",
    "43-9021", "43-4051", "43-3031", "43-6014", "43-4161", "43-2011",
    "27-3042", "27-3043", "27-3091", "27-3092",
)

DEFS = {}
DEFS["(a) manuscript definition"] = occ.onetsoc.str.startswith(
    ("15-12", "43-", "27-30", "13-20", "15-20"))
DEFS["(b) computer and mathematical only"] = occ.onetsoc.str.startswith(
    ("15-12", "15-20"))
DEFS["(c) manuscript, screened office support"] = (
    DEFS["(a) manuscript definition"] & ~occ.onetsoc.isin(NON_OFFSHORABLE_43))
DEFS["(d) core BPO and freelancing"] = occ.onetsoc.str.startswith(CORE_BPO)
DEFS["(e) computer plus writing and translation"] = occ.onetsoc.str.startswith(
    ("15-12", "27-30"))

w("=" * 78)
w("A. BUNDLE SENSITIVITY")
w("=" * 78)
rows = []
for k, mask in DEFS.items():
    sel = occ[mask]
    rows.append(dict(definition=k, n=len(sel), beta=sel.beta.mean(),
                     beta_h=sel.beta_h.mean(), sd=sel.beta.std(ddof=1),
                     median=sel.beta.median()))
bt = pd.DataFrame(rows)
base_mean = occ.loc[occ.base, "beta"].mean()
bt["ratio_to_base"] = bt.beta / base_mean
w(bt.to_string(index=False, float_format=lambda x: f"{x:8.3f}"))
w(f"\nComparison bundle (physical and non-tradable): mean {base_mean:.3f}, "
  f"n = {int(occ.base.sum())}")
w(f"Occupations dropped from (a) to reach (c): "
  f"{int(DEFS['(a) manuscript definition'].sum() - DEFS['(c) manuscript, screened office support'].sum())}")

# ---------------------------------------------------------------------------
# B. Inference that respects the structure of the data
# ---------------------------------------------------------------------------
w("\n" + "=" * 78)
w("B. INFERENCE")
w("=" * 78)
bundle = occ[DEFS["(a) manuscript definition"]]
base = occ[occ.base]
obs_diff = bundle.beta.mean() - base.beta.mean()
w(f"\nObserved difference in means: {obs_diff:.4f}")

# Cluster bootstrap on SOC minor groups: occupations within a minor group share
# task content, so they are not independent observations.
pool = pd.concat([bundle.assign(grp="bundle"), base.assign(grp="base")])
clusters = {g: d for g, d in pool.groupby("soc_minor")}
keys = list(clusters)
B = 10000
draws = np.empty(B)
for b in range(B):
    samp = pd.concat([clusters[keys[i]] for i in
                      rng.integers(0, len(keys), len(keys))])
    a = samp.loc[samp.grp == "bundle", "beta"]
    c = samp.loc[samp.grp == "base", "beta"]
    draws[b] = a.mean() - c.mean() if len(a) and len(c) else np.nan
draws = draws[~np.isnan(draws)]
lo, hi = np.percentile(draws, [2.5, 97.5])
w(f"Cluster bootstrap on SOC minor group, {len(draws)} resamples: "
  f"95% interval [{lo:.4f}, {hi:.4f}]")

# Permutation test that reassigns whole minor groups rather than occupations.
grp_labels = pool.groupby("soc_minor").grp.first()
n_bundle_grps = int((grp_labels == "bundle").sum())
perm = np.empty(B)
gk = list(grp_labels.index)
for b in range(B):
    shuffled = rng.permutation(gk)
    bg = set(shuffled[:n_bundle_grps])
    a = pool.loc[pool.soc_minor.isin(bg), "beta"]
    c = pool.loc[~pool.soc_minor.isin(bg), "beta"]
    perm[b] = a.mean() - c.mean()
p = float((np.abs(perm) >= abs(obs_diff)).mean())
w(f"Group-level permutation test, {B} draws: p = {p:.4f} "
  f"({n_bundle_grps} of {len(gk)} minor groups assigned to the bundle)")

# ---------------------------------------------------------------------------
# C. Distributional statistics
# ---------------------------------------------------------------------------
w("\n" + "=" * 78)
w("C. DISTRIBUTIONS WITHIN BUNDLES")
w("=" * 78)
for lab, d in [("pathway bundle", bundle.beta), ("physical base", base.beta)]:
    q = d.quantile([0.10, 0.25, 0.50, 0.75, 0.90])
    w(f"{lab:16s} n={len(d):4d}  mean {d.mean():.3f}  sd {d.std(ddof=1):.3f}  "
      f"p10 {q[0.10]:.3f}  p25 {q[0.25]:.3f}  median {q[0.50]:.3f}  "
      f"p75 {q[0.75]:.3f}  p90 {q[0.90]:.3f}")
w(f"Share of pathway occupations with beta below the base mean "
  f"({base_mean:.3f}): {100*(bundle.beta < base_mean).mean():.1f}%")
w(f"Share of base occupations with beta above the pathway mean "
  f"({bundle.beta.mean():.3f}): {100*(base.beta > bundle.beta.mean()).mean():.1f}%")

# ---------------------------------------------------------------------------
# D. Age-of-entry sensitivity
# ---------------------------------------------------------------------------
w("\n" + "=" * 78)
w("D. AGE OF LABOUR MARKET ENTRY")
w("=" * 78)
UNCODE = {"EGY": 818, "ETH": 231, "GHA": 288, "KEN": 404, "NGA": 566,
          "RWA": 646, "SEN": 686, "TZA": 834, "UGA": 800, "ZAF": 710}
r = pyreadr.read_r(os.path.join(DATA, "popprojAge1dt.rda"))
proj = list(r.values())[0]
proj["year"] = proj["year"].astype(int)
sel = proj[(proj.country_code.isin(list(UNCODE.values()) + [903])) &
           (proj.year.between(2025, 2050))].copy()
sel["entrants"] = (sel.popM + sel.popF) * 1000.0
for age in (15, 18, 20):
    ten = sel[(sel.age == age) & (sel.country_code.isin(UNCODE.values()))]
    afr = sel[(sel.age == age) & (sel.country_code == 903)]
    w(f"age {age}: ten economies mean {ten.groupby('year').entrants.sum().mean():,.0f} "
      f"per year, cumulative {ten.entrants.sum():,.0f}; "
      f"Africa mean {afr.groupby('year').entrants.sum().mean():,.0f} per year")

with open(os.path.join(OUT, "results_robustness.txt"), "w") as fh:
    fh.write("\n".join(lines))
bt.to_csv(os.path.join(OUT, "bundle_sensitivity.csv"), index=False)
print("\nwrote results/results_robustness.txt")
