"""Supplementary computations and robustness checks."""
import os, glob
import numpy as np
import pandas as pd
import pyreadr

DATA = "data"; OUT = "results"
AFR10 = ["EGY","ETH","GHA","KEN","NGA","RWA","SEN","TZA","UGA","ZAF"]

frames = [pd.read_csv(f, comment="#") for f in sorted(glob.glob(os.path.join(DATA,"wdi_raw_*.csv")))]
wdi = pd.concat(frames, ignore_index=True)
wdi["value"] = pd.to_numeric(wdi["value"], errors="coerce")
wdi = wdi.dropna(subset=["value"]).drop_duplicates(["indicator","iso3","year"])
def wide(i): return wdi[wdi.indicator==i].pivot(index="year", columns="iso3", values="value")

occ = pd.read_csv(os.path.join(DATA,"occ_level.csv")).rename(
    columns={"O*NET-SOC Code":"onetsoc","Title":"title"})
jz = pd.read_csv(os.path.join(DATA,"onet_jobzones.csv"))
occ = occ.merge(jz, on="onetsoc", how="left")
occ["soc_major"] = occ.onetsoc.str[:2]
occ["beta"] = occ["dv_rating_beta"]
BUNDLE = ("15-12","43-","27-30","13-20","15-20")
occ["bundle"] = occ.onetsoc.map(lambda c: any(c.startswith(p) for p in BUNDLE))
BASE = {"31","33","35","37","39","41","45","47","49","51","53"}
occ["base"] = occ.soc_major.isin(BASE)

lines = []
def w(*a):
    s = " ".join(str(x) for x in a); print(s); lines.append(s)

# ---- Aggregate ICT service exports, ten economies -------------------------
ict = wide("BX.GSR.CCIS.CD.MN")
agg = {}
for y in range(2010, 2025):
    vals = [ict[c].get(y, np.nan) for c in AFR10 if c in ict.columns]
    obs = [v for v in vals if not np.isnan(v)]
    agg[y] = (np.nansum(vals), len(obs))
w("Aggregate ICT service exports (US$ m), ten economies, with n reporting:")
for y, (v, n) in agg.items():
    w(f"  {y}: {v:9,.0f}  (n={n})")

bal = [c for c in AFR10 if c in ict.columns and
       not np.isnan(ict[c].get(2015, np.nan)) and not np.isnan(ict[c].get(2024, np.nan))]
w("\nBalanced panel 2015-2024:", bal)
for y in (2015, 2019, 2021, 2022, 2023, 2024):
    w(f"  {y}: {sum(ict[c].get(y, np.nan) for c in bal):9,.0f}")
b15 = sum(ict[c].get(2015, np.nan) for c in bal)
b21 = sum(ict[c].get(2021, np.nan) for c in bal)
b24 = sum(ict[c].get(2024, np.nan) for c in bal)
w(f"  CAGR 2015-2021: {((b21/b15)**(1/6)-1)*100:5.2f}%   "
  f"CAGR 2021-2024: {((b24/b21)**(1/3)-1)*100:5.2f}%")
ex_za = [c for c in bal if c != "ZAF"]
e15 = sum(ict[c].get(2015, np.nan) for c in ex_za)
e21 = sum(ict[c].get(2021, np.nan) for c in ex_za)
e24 = sum(ict[c].get(2024, np.nan) for c in ex_za)
w(f"  Excluding South Africa: CAGR 2015-2021 {((e21/e15)**(1/6)-1)*100:5.2f}%, "
  f"2021-2024 {((e24/e21)**(1/3)-1)*100:5.2f}%")

# ---- Absorption requirement ----------------------------------------------
entr_annual = 19_607_363     # from analysis.py, UN WPP 2024
tot24 = sum(ict[c].get(2024, np.nan) for c in AFR10 if c in ict.columns
            and not np.isnan(ict[c].get(2024, np.nan)))
w(f"\nICT service exports 2024, ten economies: US${tot24:,.0f} m")
for tgt in (0.05, 0.10, 0.25):
    for rpw in (8000, 15000, 30000):
        need = entr_annual * tgt * rpw / 1e6
        w(f"  absorbing {tgt*100:4.0f}% of one annual cohort at ${rpw:,}/worker "
          f"requires US${need:,.0f} m of annual exports = {need/tot24:5.1f}x the 2024 level")

# ---- Robustness on the exposure gap --------------------------------------
w("\nRobustness of the exposure gap:")
for lab, col in [("GPT-4 rated beta","dv_rating_beta"),
                 ("human rated beta","human_rating_beta"),
                 ("GPT-4 alpha (E1 only)","dv_rating_alpha"),
                 ("GPT-4 gamma (E1+E2)","dv_rating_gamma")]:
    a = occ.loc[occ.bundle, col].mean(); b = occ.loc[occ.base, col].mean()
    w(f"  {lab:24s} bundle {a:.3f}  base {b:.3f}  ratio {a/b:5.2f}  gap {a-b:.3f}")

narrow = occ[occ.onetsoc.str.startswith(("15-12","43-"))]
w(f"  Narrow bundle (computer + office support only): mean {narrow.beta.mean():.3f}, "
  f"n={len(narrow)}")

# ---- Which occupations anchor the bundle ---------------------------------
top = occ[occ.bundle].nlargest(12, "beta")[["onetsoc","title","beta","jobzone"]]
w("\nMost exposed occupations within the tradable cognitive bundle:")
w(top.to_string(index=False, float_format=lambda x: f"{x:5.2f}"))
low = occ[occ.bundle].nsmallest(8, "beta")[["onetsoc","title","beta","jobzone"]]
w("\nLeast exposed occupations within the bundle:")
w(low.to_string(index=False, float_format=lambda x: f"{x:5.2f}"))

# ---- Sector mapping robustness -------------------------------------------
def stock(country, eng_in_industry):
    agr = wide("SL.AGR.EMPL.ZS")[country].get(2024)
    ind = wide("SL.IND.EMPL.ZS")[country].get(2024)
    srv = wide("SL.SRV.EMPL.ZS")[country].get(2024)
    t = agr+ind+srv
    sec = {}
    for m in occ.soc_major.unique():
        if m == "45": sec[m] = "agriculture"
        elif m in {"47","49","51"}: sec[m] = "industry"
        elif eng_in_industry and m in {"17","19"}: sec[m] = "industry"
        else: sec[m] = "services"
    e = occ.assign(s=occ.soc_major.map(sec)).groupby("s").beta.mean()
    return (agr/t)*e["agriculture"] + (ind/t)*e["industry"] + (srv/t)*e["services"]

w("\nStock-exposure robustness (engineering and science occupations reassigned):")
for c in AFR10:
    w(f"  {c}: baseline {stock(c, False):.3f}   17/19 in industry {stock(c, True):.3f}")

with open(os.path.join(OUT,"results_supplementary.txt"),"w") as fh:
    fh.write("\n".join(lines))
print("\nwrote results/results_supplementary.txt")
