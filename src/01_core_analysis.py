"""
Premature de-laborization: empirical analysis.

Data sources (all retrieved 2026-09-20):
  * World Bank, World Development Indicators (api.worldbank.org/v2)
  * Eloundou, Manning, Mishkin & Rock (2024), occupation-level GPT exposure
    scores, replication repository openai/GPTs-are-GPTs, file data/occ_level.csv
  * O*NET 29.1 database, Job Zones.txt (onetcenter.org)
  * United Nations, World Population Prospects 2024, R data package wpp2024
    (PPgp/wpp2024), object popprojAge1dt

Outputs: tables (CSV + LaTeX) and figures in ../figs
"""

import glob
import os
import numpy as np
import pandas as pd
import pyreadr

pd.set_option("display.width", 200)

DATA = "data"
FIGS = "figures"
OUT = "results"
os.makedirs(FIGS, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

AFR10 = ["EGY", "ETH", "GHA", "KEN", "NGA", "RWA", "SEN", "TZA", "UGA", "ZAF"]
COMP = ["BGD", "CHN", "IND", "KOR", "MYS", "VNM"]
NAME = {
    "EGY": "Egypt", "ETH": "Ethiopia", "GHA": "Ghana", "KEN": "Kenya",
    "NGA": "Nigeria", "RWA": "Rwanda", "SEN": "Senegal", "TZA": "Tanzania",
    "UGA": "Uganda", "ZAF": "South Africa", "BGD": "Bangladesh", "CHN": "China",
    "IND": "India", "KOR": "Korea, Rep.", "MYS": "Malaysia", "VNM": "Viet Nam",
}
UNCODE = {"EGY": 818, "ETH": 231, "GHA": 288, "KEN": 404, "NGA": 566,
          "RWA": 646, "SEN": 686, "TZA": 834, "UGA": 800, "ZAF": 710}

# ----------------------------------------------------------------------------
# 1. Load the WDI panel
# ----------------------------------------------------------------------------

frames = []
for f in sorted(glob.glob(os.path.join(DATA, "wdi_raw_*.csv"))):
    frames.append(pd.read_csv(f, comment="#"))
wdi = pd.concat(frames, ignore_index=True)
wdi["value"] = pd.to_numeric(wdi["value"], errors="coerce")
wdi = wdi.dropna(subset=["value"]).drop_duplicates(["indicator", "iso3", "year"])


def series(ind, iso=None):
    d = wdi[wdi.indicator == ind]
    if iso:
        d = d[d.iso3 == iso]
    return d.sort_values("year")


def wide(ind):
    return series(ind).pivot(index="year", columns="iso3", values="value")


# ----------------------------------------------------------------------------
# 2. Occupational exposure and job zones
# ----------------------------------------------------------------------------

occ = pd.read_csv(os.path.join(DATA, "occ_level.csv"))
occ = occ.rename(columns={"O*NET-SOC Code": "onetsoc", "Title": "title"})
jz = pd.read_csv(os.path.join(DATA, "onet_jobzones.csv"))
occ = occ.merge(jz, on="onetsoc", how="left")
occ["soc_major"] = occ.onetsoc.str[:2]
occ["soc_minor"] = occ.onetsoc.str[:5]

# beta = E1 + 0.5*E2, the central exposure measure in Eloundou et al. (2024).
occ["beta_gpt4"] = occ["dv_rating_beta"]
occ["beta_human"] = occ["human_rating_beta"]

MAJOR_LABEL = {
    "11": "Management", "13": "Business and financial operations",
    "15": "Computer and mathematical", "17": "Architecture and engineering",
    "19": "Life, physical and social science", "21": "Community and social service",
    "23": "Legal", "25": "Educational instruction and library",
    "27": "Arts, design, entertainment, sports and media",
    "29": "Healthcare practitioners and technical", "31": "Healthcare support",
    "33": "Protective service", "35": "Food preparation and serving",
    "37": "Building and grounds cleaning and maintenance",
    "39": "Personal care and service", "41": "Sales and related",
    "43": "Office and administrative support",
    "45": "Farming, fishing and forestry", "47": "Construction and extraction",
    "49": "Installation, maintenance and repair", "51": "Production",
    "53": "Transportation and material moving",
}
occ["major_label"] = occ.soc_major.map(MAJOR_LABEL)

# --- 2a. The tradable entry-level cognitive services bundle --------------
# The occupational content of the service-led digital development pathway:
# business process outsourcing, online freelancing and junior offshore
# software work. Defined ex ante from SOC minor groups.
BUNDLE_PREFIX = ("15-12", "43-", "27-30", "13-20", "15-20")


def in_bundle(code):
    return any(code.startswith(p) for p in BUNDLE_PREFIX)


occ["tradable_cognitive"] = occ.onetsoc.map(in_bundle)

# Occupations that dominate employment in low-income African labour markets:
# agriculture, construction, production, transport, personal and protective
# services, sales.
BASE_MAJORS = {"31", "33", "35", "37", "39", "41", "45", "47", "49", "51", "53"}
occ["subsistence_base"] = occ.soc_major.isin(BASE_MAJORS)

# --- 2b. Sector mapping (ISIC-aligned) -----------------------------------
SECTOR = {}
for m in MAJOR_LABEL:
    if m == "45":
        SECTOR[m] = "agriculture"
    elif m in {"47", "49", "51"}:
        SECTOR[m] = "industry"
    else:
        SECTOR[m] = "services"
occ["sector"] = occ.soc_major.map(SECTOR)

sector_exposure = occ.groupby("sector").beta_gpt4.agg(["mean", "std", "count"])
sector_exposure_h = occ.groupby("sector").beta_human.mean()

# ----------------------------------------------------------------------------
# 3. Results
# ----------------------------------------------------------------------------

res = {}

# --- 3.1 Exposure by SOC major group -------------------------------------
maj = (occ.groupby(["soc_major", "major_label"])
       .agg(n=("beta_gpt4", "size"),
            beta_gpt4=("beta_gpt4", "mean"),
            beta_human=("beta_human", "mean"),
            jobzone=("jobzone", "mean"))
       .reset_index().sort_values("beta_gpt4", ascending=False))
res["major"] = maj

# --- 3.2 Exposure by job zone --------------------------------------------
byjz = (occ.dropna(subset=["jobzone"]).groupby("jobzone")
        .agg(n=("beta_gpt4", "size"),
             beta_gpt4=("beta_gpt4", "mean"),
             beta_human=("beta_human", "mean")).reset_index())
res["jobzone_all"] = byjz

cog = occ[occ.tradable_cognitive & occ.jobzone.notna()]
byjz_cog = (cog.groupby("jobzone")
            .agg(n=("beta_gpt4", "size"),
                 beta_gpt4=("beta_gpt4", "mean"),
                 beta_human=("beta_human", "mean")).reset_index())
res["jobzone_cognitive"] = byjz_cog

# Regression of exposure on job zone, whole economy and within the bundle.
def ols(y, x):
    x = np.asarray(x, float); y = np.asarray(y, float)
    X = np.column_stack([np.ones_like(x), x])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ b
    n, k = X.shape
    s2 = resid @ resid / (n - k)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    t = b / se
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - (resid @ resid) / ss_tot
    return b, se, t, r2, n


d_all = occ.dropna(subset=["jobzone", "beta_gpt4"])
res["ols_all"] = ols(d_all.beta_gpt4, d_all.jobzone)
res["ols_cog"] = ols(cog.beta_gpt4, cog.jobzone)
d_base = occ[occ.subsistence_base].dropna(subset=["jobzone", "beta_gpt4"])
res["ols_base"] = ols(d_base.beta_gpt4, d_base.jobzone)

# --- 3.3 Bundle comparison ------------------------------------------------
b_cog = occ[occ.tradable_cognitive].beta_gpt4
b_base = occ[occ.subsistence_base].beta_gpt4
diff = b_cog.mean() - b_base.mean()
se_diff = np.sqrt(b_cog.var(ddof=1) / len(b_cog) + b_base.var(ddof=1) / len(b_base))
res["bundle"] = dict(
    cog_mean=b_cog.mean(), cog_n=len(b_cog), cog_sd=b_cog.std(ddof=1),
    base_mean=b_base.mean(), base_n=len(b_base), base_sd=b_base.std(ddof=1),
    diff=diff, se=se_diff, t=diff / se_diff,
    cog_mean_h=occ[occ.tradable_cognitive].beta_human.mean(),
    base_mean_h=occ[occ.subsistence_base].beta_human.mean(),
)

# Entry-tier vs specialist-tier within the bundle (job zones 1-3 vs 4-5).
entry = cog[cog.jobzone <= 3].beta_gpt4
senior = cog[cog.jobzone >= 4].beta_gpt4
d2 = entry.mean() - senior.mean()
se2 = np.sqrt(entry.var(ddof=1) / len(entry) + senior.var(ddof=1) / len(senior))
res["tier"] = dict(entry_mean=entry.mean(), entry_n=len(entry),
                   senior_mean=senior.mean(), senior_n=len(senior),
                   diff=d2, se=se2, t=d2 / se2)

# --- 3.4 Stock and trajectory exposure by country -------------------------
agr = wide("SL.AGR.EMPL.ZS")
ind = wide("SL.IND.EMPL.ZS")
srv = wide("SL.SRV.EMPL.ZS")

e_agr = sector_exposure.loc["agriculture", "mean"]
e_ind = sector_exposure.loc["industry", "mean"]
e_srv = sector_exposure.loc["services", "mean"]
e_bundle = b_cog.mean()

rows = []
for c in AFR10:
    yr = 2024
    a = agr[c].get(yr, np.nan)
    i = ind[c].get(yr, np.nan)
    s = srv[c].get(yr, np.nan)
    tot = a + i + s
    a, i, s = a / tot, i / tot, s / tot
    stock = a * e_agr + i * e_ind + s * e_srv
    rows.append(dict(iso3=c, country=NAME[c], agr=a * 100, ind=i * 100, srv=s * 100,
                     stock_exposure=stock, trajectory_exposure=e_bundle,
                     ratio=e_bundle / stock))
expo = pd.DataFrame(rows).sort_values("ratio", ascending=False)
res["exposure_country"] = expo

# --- 3.5 Premature deindustrialisation ------------------------------------
manf = wide("NV.IND.MANF.ZS")
gdp = wide("NY.GDP.PCAP.PP.KD")
rows = []
for c in AFR10 + COMP:
    if c not in manf.columns:
        continue
    s = manf[c].dropna()
    if s.empty:
        continue
    pk_year = int(s.idxmax())
    pk_val = s.max()
    g = gdp[c].get(pk_year, np.nan) if c in gdp.columns else np.nan
    cur = s.loc[s.index.max()]
    rows.append(dict(iso3=c, country=NAME[c], group="Africa" if c in AFR10 else "Comparator",
                     peak_year=pk_year, peak_manf=pk_val, gdppc_at_peak=g,
                     latest_year=int(s.index.max()), latest_manf=cur,
                     decline=pk_val - cur))
peaks = pd.DataFrame(rows).sort_values(["group", "peak_manf"], ascending=[True, False])
res["peaks"] = peaks

# --- 3.6 ICT service exports ----------------------------------------------
ict = wide("BX.GSR.CCIS.CD.MN")
rows = []
for c in AFR10:
    s = ict[c].dropna() if c in ict.columns else pd.Series(dtype=float)
    if s.empty:
        continue
    def g(y):
        return s.get(y, np.nan)
    def cagr(y0, y1):
        a, b = g(y0), g(y1)
        if np.isnan(a) or np.isnan(b) or a <= 0:
            return np.nan
        return (b / a) ** (1 / (y1 - y0)) - 1
    rows.append(dict(iso3=c, country=NAME[c], v2015=g(2015), v2019=g(2019),
                     v2021=g(2021), v2022=g(2022), v2024=g(2024),
                     cagr_15_21=cagr(2015, 2021) * 100,
                     cagr_21_24=cagr(2021, 2024) * 100))
ictt = pd.DataFrame(rows)
res["ict"] = ictt

lf = wide("SL.TLF.TOTL.IN")
ict_total_2024 = float(np.nansum([ict[c].get(2024, np.nan) for c in AFR10 if c in ict.columns]))
lf_total_2024 = float(np.nansum([lf[c].get(2024, np.nan) for c in AFR10 if c in lf.columns]))
res["ict_total_2024"] = ict_total_2024
res["lf_total_2024"] = lf_total_2024

# --- 3.7 Demographic arithmetic -------------------------------------------
r = pyreadr.read_r(os.path.join(DATA, "popprojAge1dt.rda"))
proj = list(r.values())[0]
proj["year"] = proj["year"].astype(int)
ent = proj[(proj.age == 20) & (proj.year.between(2025, 2050))].copy()
ent["entrants"] = (ent.popM + ent.popF) * 1000.0   # source is in thousands

ent10 = ent[ent.country_code.isin(UNCODE.values())]
rev = {v: k for k, v in UNCODE.items()}
ent10 = ent10.assign(iso3=ent10.country_code.map(rev))
entrants_by_country = (ent10.groupby("iso3").entrants
                       .agg(annual_mean="mean", total="sum").reset_index())
entrants_by_country["country"] = entrants_by_country.iso3.map(NAME)
res["entrants"] = entrants_by_country.sort_values("annual_mean", ascending=False)

afr = ent[ent.country_code == 903]
res["africa_entrants_annual"] = float(afr.groupby("year").entrants.sum().mean())
res["africa_entrants_total"] = float(afr.entrants.sum())
res["ten_entrants_annual"] = float(entrants_by_country.annual_mean.sum())
res["ten_entrants_total"] = float(entrants_by_country.total.sum())

# Absorption arithmetic: jobs supported by the entire ICT service export
# sector at alternative levels of export revenue per worker.
absorption = []
for rpw in (8000, 15000, 30000):
    jobs = ict_total_2024 * 1e6 / rpw
    absorption.append(dict(revenue_per_worker=rpw, jobs=jobs,
                           pct_of_labour_force=100 * jobs / lf_total_2024,
                           share_of_one_year_entrants=100 * jobs / res["ten_entrants_annual"]))
res["absorption"] = pd.DataFrame(absorption)

# ----------------------------------------------------------------------------
# 4. Report
# ----------------------------------------------------------------------------

with open(os.path.join(OUT, "results.txt"), "w") as fh:
    def w(*a):
        s = " ".join(str(x) for x in a)
        print(s)
        fh.write(s + "\n")

    w("=" * 78)
    w("SECTION A. OCCUPATIONAL EXPOSURE")
    w("=" * 78)
    w("\nA1. Mean exposure (beta) by SOC major group, n =", len(occ))
    w(maj.to_string(index=False, float_format=lambda x: f"{x:6.3f}"))

    w("\nA2. Sector-level mean exposure (ISIC-aligned mapping)")
    w(sector_exposure.to_string(float_format=lambda x: f"{x:6.3f}"))
    w("human-rated:", sector_exposure_h.round(3).to_dict())

    w("\nA3. Exposure by O*NET Job Zone, all occupations")
    w(byjz.to_string(index=False, float_format=lambda x: f"{x:6.3f}"))
    w("\nA4. Exposure by Job Zone, tradable cognitive bundle only")
    w(byjz_cog.to_string(index=False, float_format=lambda x: f"{x:6.3f}"))

    for k, lab in [("ols_all", "all occupations"),
                   ("ols_cog", "tradable cognitive bundle"),
                   ("ols_base", "subsistence/physical base")]:
        b, se, t, r2, n = res[k]
        w(f"\nA5. OLS beta ~ jobzone ({lab}): slope={b[1]:.4f} (se {se[1]:.4f}, "
          f"t={t[1]:.2f}), intercept={b[0]:.4f}, R2={r2:.3f}, n={n}")

    bd = res["bundle"]
    w(f"\nA6. Bundle means. Tradable cognitive: {bd['cog_mean']:.3f} "
      f"(sd {bd['cog_sd']:.3f}, n={bd['cog_n']}). "
      f"Physical/subsistence base: {bd['base_mean']:.3f} "
      f"(sd {bd['base_sd']:.3f}, n={bd['base_n']}). "
      f"Difference {bd['diff']:.3f} (se {bd['se']:.3f}, t={bd['t']:.2f}).")
    w(f"    Human-rated equivalents: {bd['cog_mean_h']:.3f} vs {bd['base_mean_h']:.3f}.")

    td = res["tier"]
    w(f"\nA7. Within the bundle, job zones 1-3 mean {td['entry_mean']:.3f} "
      f"(n={td['entry_n']}) vs job zones 4-5 mean {td['senior_mean']:.3f} "
      f"(n={td['senior_n']}); difference {td['diff']:.3f} "
      f"(se {td['se']:.3f}, t={td['t']:.2f}).")

    w("\n" + "=" * 78)
    w("SECTION B. STOCK VERSUS TRAJECTORY EXPOSURE")
    w("=" * 78)
    w(expo.to_string(index=False, float_format=lambda x: f"{x:7.3f}"))

    w("\n" + "=" * 78)
    w("SECTION C. PREMATURE DEINDUSTRIALISATION")
    w("=" * 78)
    w(peaks.to_string(index=False, float_format=lambda x: f"{x:9.2f}"))
    afr_p = peaks[peaks.group == "Africa"]
    cmp_p = peaks[peaks.group == "Comparator"]
    w(f"\nMean peak manufacturing VA share: Africa {afr_p.peak_manf.mean():.2f}% "
      f"at mean GDP per capita ${afr_p.gdppc_at_peak.mean():,.0f}; "
      f"comparators {cmp_p.peak_manf.mean():.2f}% at ${cmp_p.gdppc_at_peak.mean():,.0f}.")

    w("\n" + "=" * 78)
    w("SECTION D. THE DIGITAL SERVICES CHANNEL")
    w("=" * 78)
    w(ictt.to_string(index=False, float_format=lambda x: f"{x:9.2f}"))
    w(f"\nTotal ICT service exports, ten economies, 2024: "
      f"US${ict_total_2024:,.0f} million.")
    w(f"Combined labour force, 2024: {lf_total_2024:,.0f}.")
    w("\nAbsorption arithmetic:")
    w(res["absorption"].to_string(index=False, float_format=lambda x: f"{x:14.2f}"))

    w("\n" + "=" * 78)
    w("SECTION E. DEMOGRAPHIC ARITHMETIC (UN WPP 2024, medium variant)")
    w("=" * 78)
    w(res["entrants"].to_string(index=False, float_format=lambda x: f"{x:,.0f}"))
    w(f"\nTen economies: mean {res['ten_entrants_annual']:,.0f} people reach age 20 "
      f"each year, 2025-2050; cumulative {res['ten_entrants_total']:,.0f}.")
    w(f"Africa as a whole: mean {res['africa_entrants_annual']:,.0f} per year; "
      f"cumulative {res['africa_entrants_total']:,.0f}.")

for k, v in res.items():
    if isinstance(v, pd.DataFrame):
        v.to_csv(os.path.join(OUT, f"{k}.csv"), index=False)

print("\nWrote", OUT)
