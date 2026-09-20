"""
Online Labour Index: compositional test of the trajectory-exposure argument.

Data: OLI_microwork_data_2024-08-22.txt, Figshare deposit 10.6084/m9.figshare.3761562
      (Kassi & Lehdonvirta). Daily counts of NEW vacancies by occupation across
      the major English-language online labour platforms, normalised so that
      mean daily vacancies in May 2016 = 100.

Question: after the commercial release of general-purpose models, did demand
shift away from the occupational categories our exposure measure identifies as
most automatable?

Note on interpretation: the OLI is a demand-side index of vacancies, not of
African supplier contracts. It tests the mechanism globally; it does not by
itself establish an effect on African suppliers.
"""

import os
import numpy as np
import pandas as pd

DATA, OUT = "data", "results"
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. OLI demand series
# ---------------------------------------------------------------------------
m = pd.read_csv(os.path.join(DATA, "oli_microwork.txt.gz"), parse_dates=["date"])
new = m[m.status == "new"]
daily = new.pivot_table(index="date", columns="occupation", values="count",
                        aggfunc="sum")
OCCS = [c for c in daily.columns if c != "Total"]
monthly = daily.resample("MS").mean()

# Shares of the occupational total (Total is the sum of the seven categories).
shares = monthly[OCCS].div(monthly["Total"], axis=0) * 100

# ---------------------------------------------------------------------------
# 2. Map OLI categories onto the SOC exposure data
# ---------------------------------------------------------------------------
occ = pd.read_csv(os.path.join(DATA, "occ_level.csv")).rename(
    columns={"O*NET-SOC Code": "onetsoc", "Title": "title"})
occ["beta"] = occ["dv_rating_beta"]
occ["beta_h"] = occ["human_rating_beta"]

# Documented, ex ante mapping from the OLI taxonomy to SOC prefixes.
OLI_TO_SOC = {
    "Software development and technology": ("15-12",),
    "Clerical and data entry":             ("43-",),
    "Writing and translation":             ("27-30",),
    "Creative and multimedia":             ("27-1", "27-4"),
    "Professional services":               ("13-", "23-"),
    "Sales and marketing support":         ("41-",),
    "Microwork":                           ("43-9021", "43-9061"),
}


def bundle_beta(prefixes, col="beta"):
    sel = occ[occ.onetsoc.str.startswith(prefixes)]
    return sel[col].mean(), len(sel)


expo = {}
for k, pref in OLI_TO_SOC.items():
    b, n = bundle_beta(pref)
    bh, _ = bundle_beta(pref, "beta_h")
    expo[k] = dict(beta=b, beta_h=bh, n_soc=n)
expo_df = pd.DataFrame(expo).T.sort_values("beta", ascending=False)

# ---------------------------------------------------------------------------
# 3. Pre and post windows
# ---------------------------------------------------------------------------
# ChatGPT was released on 30 November 2022. We leave Nov and Dec 2022 out as a
# transition window. 2024 stops in August, so the like-for-like comparison uses
# January to August in every year.
def jan_aug(df, years):
    s = df[(df.index.month <= 8) & (df.index.year.isin(years))]
    return s.mean()


PRE_YEARS = [2019, 2020, 2021, 2022]
POST_YEARS = [2023, 2024]

pre_sh, post_sh = jan_aug(shares, PRE_YEARS), jan_aug(shares, POST_YEARS)
pre_lv, post_lv = jan_aug(monthly, PRE_YEARS), jan_aug(monthly, POST_YEARS)

res = pd.DataFrame({
    "beta": [expo[o]["beta"] for o in OCCS],
    "share_pre": pre_sh[OCCS],
    "share_post": post_sh[OCCS],
    "level_pre": pre_lv[OCCS],
    "level_post": post_lv[OCCS],
})
res["share_change_pp"] = res.share_post - res.share_pre
res["level_change_pct"] = 100 * (res.level_post / res.level_pre - 1)
total_change = 100 * (post_lv["Total"] / pre_lv["Total"] - 1)
res["relative_to_total_pct"] = res.level_change_pct - total_change
res = res.sort_values("beta", ascending=False)

# Correlation between exposure and the relative demand change.
r_share = np.corrcoef(res.beta, res.share_change_pp)[0, 1]
r_rel = np.corrcoef(res.beta, res.relative_to_total_pct)[0, 1]

# Rank correlation, which is the honest statistic at n = 7.
def spearman(x, y):
    rx = pd.Series(x).rank()
    ry = pd.Series(y).rank()
    return np.corrcoef(rx, ry)[0, 1]


rho_share = spearman(res.beta, res.share_change_pp)
rho_rel = spearman(res.beta, res.relative_to_total_pct)

# ---------------------------------------------------------------------------
# 4. Demand-weighted trajectory exposure
# ---------------------------------------------------------------------------
# The unweighted occupational mean in the manuscript is 0.656. Weighting by the
# observed composition of online labour demand answers the equal-weighting
# objection directly.
def weighted_exposure(share_series, col="beta"):
    w = share_series[OCCS] / share_series[OCCS].sum()
    return sum(w[o] * expo[o][col] for o in OCCS)


te_pre = weighted_exposure(pre_sh)
te_post = weighted_exposure(post_sh)
te_pre_h = weighted_exposure(pre_sh, "beta_h")

# Excluding microwork, which has no clean SOC analogue.
OCCS_NM = [o for o in OCCS if o != "Microwork"]
w_nm = pre_sh[OCCS_NM] / pre_sh[OCCS_NM].sum()
te_pre_nm = sum(w_nm[o] * expo[o]["beta"] for o in OCCS_NM)

# ---------------------------------------------------------------------------
# 5. Report
# ---------------------------------------------------------------------------
lines = []
def w(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    lines.append(s)


w("=" * 78)
w("ONLINE LABOUR INDEX: DEMAND COMPOSITION AND EXPOSURE")
w("=" * 78)
w("\nSeries: daily new vacancies, May 2016 = 100. Coverage",
  daily.index.min().date(), "to", daily.index.max().date())
w("\n1. Exposure of each OLI occupational category (SOC mapping)")
w(expo_df.to_string(float_format=lambda x: f"{x:7.3f}"))

w("\n2. Demand composition, January to August, "
  f"pre = {PRE_YEARS}, post = {POST_YEARS}")
w(res.to_string(float_format=lambda x: f"{x:9.2f}"))
w(f"\n   Total index change over the same windows: {total_change:.2f}%")

w("\n3. Does exposure predict the demand change? (n = %d categories)" % len(res))
w(f"   Pearson r, exposure vs change in share:            {r_share: .3f}")
w(f"   Pearson r, exposure vs change relative to total:   {r_rel: .3f}")
w(f"   Spearman rho, exposure vs change in share:         {rho_share: .3f}")
w(f"   Spearman rho, exposure vs relative change:         {rho_rel: .3f}")

w("\n4. Demand-weighted trajectory exposure")
w(f"   Unweighted occupational mean (manuscript):         0.656")
w(f"   OLI demand-weighted, pre-release composition:      {te_pre:.3f}")
w(f"   OLI demand-weighted, post-release composition:     {te_post:.3f}")
w(f"   OLI demand-weighted, human ratings, pre:           {te_pre_h:.3f}")
w(f"   OLI demand-weighted, excluding microwork, pre:     {te_pre_nm:.3f}")

w("\n5. Annual means, January to August, by occupation")
ja = monthly[monthly.index.month <= 8]
w(ja.groupby(ja.index.year).mean().round(1).to_string())

with open(os.path.join(OUT, "results_oli.txt"), "w") as fh:
    fh.write("\n".join(lines))
res.to_csv(os.path.join(OUT, "oli_composition.csv"))
shares.to_csv(os.path.join(OUT, "oli_shares_monthly.csv"))
monthly.to_csv(os.path.join(OUT, "oli_levels_monthly.csv"))
expo_df.to_csv(os.path.join(OUT, "oli_category_exposure.csv"))
print("\nwrote results/results_oli.txt")
