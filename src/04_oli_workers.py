"""
Online Labour Index worker supplement: the exposure of the African online
labour portfolio, by country and over time.

Data: worker_countrydata_2024-09-02.txt.gz and Countries_continents_regions.txt,
Figshare deposit 10.6084/m9.figshare.3761562 (Kassi & Lehdonvirta).

Weighted sample of recently active worker profiles from Guru, Freelancer (from
January 2019), PeoplePerHour and Fiverr (to January 2018), weighted by platform
vacancy counts.

Interpretation constraint stated by the data producers: the counts support
RELATIVE shares only, and conclusions about the level of labour supply over time
are not supported. Every quantity below is therefore a share or a
share-weighted mean, never a level.
"""

import os
import numpy as np
import pandas as pd

DATA, OUT = "data", "results"
os.makedirs(OUT, exist_ok=True)

BETA = {
    "Writing and translation": 0.759,
    "Software development and technology": 0.751,
    "Clerical and data entry": 0.608,
    "Professional services": 0.524,
    "Sales and marketing support": 0.460,
    "Creative and multimedia": 0.408,
}
OCC = list(BETA)
SAMPLE = {"Egypt": "EGY", "Ethiopia": "ETH", "Ghana": "GHA", "Kenya": "KEN",
          "Nigeria": "NGA", "Rwanda": "RWA", "Senegal": "SEN",
          "Tanzania": "TZA", "Uganda": "UGA", "South Africa": "ZAF"}

w = pd.read_csv(os.path.join(DATA, "worker_countrydata_2024-09-02.txt.gz"),
                parse_dates=["timestamp"])
reg = pd.read_csv(os.path.join(DATA, "countries_regions.txt"),
                  sep=";").drop_duplicates("Country")
w = w.merge(reg, left_on="country", right_on="Country", how="left")
w["year"] = w.timestamp.dt.year
w["month"] = w.timestamp.dt.month
ja = w[w.month <= 8]          # like-for-like months; 2024 ends in September


def portfolio(df):
    s = df.groupby("occupation").num_workers.sum().reindex(OCC).fillna(0)
    if s.sum() == 0:
        return s, np.nan
    sh = s / s.sum()
    return sh * 100, float(sum(sh[o] * BETA[o] for o in OCC))


lines = []
def out(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    lines.append(s)


out("=" * 78)
out("OLI WORKER SUPPLEMENT: PORTFOLIO EXPOSURE")
out("=" * 78)
out("Coverage", w.timestamp.min().date(), "to", w.timestamp.max().date(),
    "|", f"{len(w):,} rows |", w.country.nunique(), "countries")

# --- by world region, recent window -----------------------------------------
recent = ja[ja.year.isin([2023, 2024])]
rows = []
for cont, d in recent.groupby("Continent"):
    _, e = portfolio(d)
    rows.append(dict(region=cont, portfolio_exposure=e,
                     share_of_world=100 * d.num_workers.sum() / recent.num_workers.sum()))
regt = pd.DataFrame(rows).sort_values("portfolio_exposure", ascending=False)
out("\n1. Portfolio exposure by world region, January to August 2023-24")
out(regt.to_string(index=False, float_format=lambda x: f"{x:10.3f}"))

# --- African occupational mix over time -------------------------------------
afr = ja[ja.Continent == "Africa"]
mix = afr.pivot_table(index="year", columns="occupation",
                      values="num_workers", aggfunc="sum")[OCC]
mix = mix.div(mix.sum(axis=1), axis=0) * 100
mix["portfolio_exposure"] = [sum(mix.loc[y, o] / 100 * BETA[o] for o in OCC)
                             for y in mix.index]
out("\n2. African occupational mix, January to August shares (%)")
out(mix.round(3).to_string())

# --- the ten sample economies ------------------------------------------------
rows = []
for c, iso in SAMPLE.items():
    d = recent[recent.country == c]
    sh, e = portfolio(d)
    r = dict(iso3=iso, country=c, trajectory_exposure_weighted=e,
             sample_workers=d.num_workers.sum())
    for o in OCC:
        r[o] = sh[o] if isinstance(sh, pd.Series) and not np.isnan(e) else np.nan
    rows.append(r)
ten = pd.DataFrame(rows).sort_values("trajectory_exposure_weighted",
                                     ascending=False)
out("\n3. Weighted trajectory exposure, ten sample economies, "
    "January to August 2023-24")
out(ten[["iso3", "country", "trajectory_exposure_weighted",
         "sample_workers"]].to_string(index=False,
                                      float_format=lambda x: f"{x:12.3f}"))
out("\n   Occupational composition (%), same window")
out(ten.set_index("iso3")[OCC].round(2).to_string())

# --- pre and post composition shift, Africa ----------------------------------
def win(df, years):
    s = df[df.year.isin(years)].groupby("occupation").num_workers.sum()
    s = s.reindex(OCC).fillna(0)
    return s / s.sum() * 100


pre, post = win(afr, [2021, 2022]), win(afr, [2023, 2024])
shift = pd.DataFrame({"beta": [BETA[o] for o in OCC],
                      "share_pre": pre, "share_post": post})
shift["change_pp"] = shift.share_post - shift.share_pre
shift = shift.sort_values("beta", ascending=False)
rho = np.corrcoef(pd.Series(shift.beta).rank(),
                  pd.Series(shift.change_pp).rank())[0, 1]
out("\n4. African supply-side composition shift, pre 2021-22 vs post 2023-24")
out(shift.to_string(float_format=lambda x: f"{x:9.3f}"))
out(f"   Spearman rho (exposure vs change in share): {rho:.3f}")
out(f"   Portfolio exposure: pre {sum(pre[o]/100*BETA[o] for o in OCC):.4f}, "
    f"post {sum(post[o]/100*BETA[o] for o in OCC):.4f}")

with open(os.path.join(OUT, "results_oli_workers.txt"), "w") as fh:
    fh.write("\n".join(lines))
regt.to_csv(os.path.join(OUT, "oli_region_portfolio.csv"), index=False)
mix.to_csv(os.path.join(OUT, "oli_africa_mix.csv"))
ten.to_csv(os.path.join(OUT, "oli_country_portfolio.csv"), index=False)
shift.to_csv(os.path.join(OUT, "oli_africa_shift.csv"))
print("\nwrote results/results_oli_workers.txt")
