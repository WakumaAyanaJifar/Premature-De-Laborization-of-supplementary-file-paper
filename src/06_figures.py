"""
All figures for the manuscript, on one validated design system.

Colour decisions follow the procedure: form first, then colour by the job it
does. Two-category comparisons use categorical slots 1 and 2 (blue, orange),
which pass the lightness, chroma, CVD-separation, normal-vision and contrast
checks on a light surface. Occupational exposure is a magnitude, so it is
encoded on a single-hue sequential blue ramp, light to dark, never a rainbow.
Identity on multi-series lines is carried by direct end labels, not by colour
alone, which also keeps the charts readable in greyscale print.
"""

import os
import glob
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

DATA, OUT, FIGS = "data", "results", "figures"
os.makedirs(FIGS, exist_ok=True)

# ---- design tokens ---------------------------------------------------------
SURFACE = "#fcfcfb"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE = "#2a78d6", "#eb6834"
# Sequential blue ramp, steps 250 to 700; step 250 is the lightest that still
# clears 2:1 against the light surface.
RAMP = ["#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
        "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
SEQ = LinearSegmentedColormap.from_list("seqblue", RAMP)

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["DejaVu Serif"],
    "font.size": 10, "axes.titlesize": 10.5, "axes.labelsize": 10,
    "legend.fontsize": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "text.color": INK, "axes.labelcolor": INK, "axes.edgecolor": AXIS,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "grid.alpha": 1.0,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "figure.dpi": 160, "savefig.dpi": 600, "savefig.bbox": "tight",
    "pdf.fonttype": 42, "ps.fonttype": 42,
})
W = 7.2  # Elsevier full text width, inches

# ---- data ------------------------------------------------------------------
frames = [pd.read_csv(f, comment="#") for f in
          sorted(glob.glob(os.path.join(DATA, "wdi_raw_*.csv")))]
wdi = pd.concat(frames, ignore_index=True)
wdi["value"] = pd.to_numeric(wdi["value"], errors="coerce")
wdi = wdi.dropna(subset=["value"]).drop_duplicates(["indicator", "iso3", "year"])
def wide(i):
    return wdi[wdi.indicator == i].pivot(index="year", columns="iso3",
                                         values="value")

peaks = pd.read_csv(os.path.join(OUT, "peaks.csv"))
major = pd.read_csv(os.path.join(OUT, "major.csv"))
jz_all = pd.read_csv(os.path.join(OUT, "jobzone_all.csv"))
jz_cog = pd.read_csv(os.path.join(OUT, "jobzone_cognitive.csv"))
expo = pd.read_csv(os.path.join(OUT, "exposure_country.csv"))
ten = pd.read_csv(os.path.join(OUT, "oli_country_portfolio.csv"))
mix = pd.read_csv(os.path.join(OUT, "oli_africa_mix.csv"), index_col=0)

occ = pd.read_csv(os.path.join(DATA, "occ_level.csv")).rename(
    columns={"O*NET-SOC Code": "onetsoc", "Title": "title"})
occ["soc_major"] = occ.onetsoc.str[:2]
occ["beta"] = occ["dv_rating_beta"]
BUNDLE = ("15-12", "43-", "27-30", "13-20", "15-20")
occ["bundle"] = occ.onetsoc.map(lambda c: any(c.startswith(p) for p in BUNDLE))
BASE = {"31", "33", "35", "37", "39", "41", "45", "47", "49", "51", "53"}
occ["base"] = occ.soc_major.isin(BASE)

BETA = {"Writing and translation": 0.759,
        "Software development and technology": 0.751,
        "Microwork": 0.734, "Clerical and data entry": 0.608,
        "Professional services": 0.524, "Sales and marketing support": 0.460,
        "Creative and multimedia": 0.408}
SHORT = {"Writing and translation": "Writing, translation",
         "Software development and technology": "Software development",
         "Microwork": "Microwork",
         "Clerical and data entry": "Clerical, data entry",
         "Professional services": "Professional services",
         "Sales and marketing support": "Sales, marketing",
         "Creative and multimedia": "Creative, multimedia"}
bnorm = plt.Normalize(0.36, 0.82)
def bcol(b):
    return SEQ(bnorm(b))


def finish(ax):
    ax.set_axisbelow(True)
    ax.tick_params(length=3, width=0.8, colors=INK2)


def panel(ax, text):
    ax.set_title(text, loc="left", color=INK, pad=7, fontweight="bold")


def end_labels(ax, series_dict, x_last, sep=0.065, fs=8.2):
    """Direct-label line ends, spaced so no two labels collide."""
    items = sorted(series_dict.items(), key=lambda kv: kv[1][1])
    lo, hi = ax.get_ylim()
    minsep = (hi - lo) * sep
    placed = []
    for _, (_, y) in items:
        placed.append(y if not placed else max(y, placed[-1] + minsep))
    over = placed[-1] - (hi - minsep * 0.3)
    if over > 0:
        placed = [q - over for q in placed]
        for i in range(len(placed) - 2, -1, -1):
            placed[i] = min(placed[i], placed[i + 1] - minsep)
    for (name, (colr, yv)), yt in zip(items, placed):
        if abs(yt - yv) > minsep * 0.25:
            ax.annotate("", xy=(x_last, yv), xytext=(x_last, yt),
                        arrowprops=dict(arrowstyle="-", color=colr, lw=0.7,
                                        alpha=0.55),
                        annotation_clip=False)
        ax.annotate(name, (x_last, yt), xytext=(9, 0),
                    textcoords="offset points", va="center", fontsize=fs,
                    color=colr, annotation_clip=False)


# =============================================================== Figure 1
LBL = {"ETH": (-4, -6, "right"), "RWA": (4, 6, "left"), "TZA": (0, 11, "center"),
       "UGA": (-6, -4, "right"), "IND": (6, -4, "left"), "SEN": (0, 11, "center"),
       "KEN": (0, -16, "center"), "NGA": (0, 11, "center"),
       "GHA": (0, -16, "center"), "CHN": (0, 11, "center"),
       "BGD": (-7, 2, "right"), "EGY": (0, 11, "center"),
       "ZAF": (7, -3, "left"), "VNM": (0, 11, "center"),
       "MYS": (0, 11, "center"), "KOR": (-7, 2, "right")}
fig, ax = plt.subplots(figsize=(W, 4.6))
for grp, col, mk, lab in [("Comparator", ORANGE, "s", "Asian comparators"),
                          ("Africa", BLUE, "o", "African economies")]:
    d = peaks[peaks.group == grp].sort_values("gdppc_at_peak")
    ax.scatter(d.gdppc_at_peak, d.peak_manf, c=col, marker=mk, s=62,
               edgecolor=SURFACE, linewidth=1.2, zorder=4, label=lab)
    for r in d.itertuples():
        dx, dy, ha = LBL.get(r.iso3, (0, 11, "center"))
        ax.annotate(r.iso3, (r.gdppc_at_peak, r.peak_manf),
                    textcoords="offset points", xytext=(dx, dy), ha=ha,
                    fontsize=8.4, color=col, fontweight="bold")
for grp, col in [("Africa", BLUE), ("Comparator", ORANGE)]:
    mval = peaks[peaks.group == grp].peak_manf.mean()
    ax.axhline(mval, color=col, ls=":", lw=1.1, zorder=1)
    ax.annotate(f"group mean {mval:.1f}%", (700, mval), xytext=(0, 4),
                textcoords="offset points", ha="left", fontsize=8.2, color=col)
ax.set_xscale("log")
ax.set_xticks([1000, 2000, 5000, 10000, 20000, 40000])
ax.get_xaxis().set_major_formatter(FuncFormatter(lambda v, p: f"{v:,.0f}"))
ax.set_xlim(620, 70000)
ax.set_ylim(0, 37)
ax.set_xlabel("GDP per capita at the manufacturing peak\n"
              "(constant 2021 international \\$, log scale)")
ax.set_ylabel("Peak manufacturing value added (% of GDP)")
ax.legend(frameon=False, loc="upper left", handletextpad=0.4,
          bbox_to_anchor=(0.015, 1.0))
finish(ax)
fig.savefig(os.path.join(FIGS, "fig1_peaks.pdf"))
plt.close(fig)

# =============================================================== Figure 2
fig, ax = plt.subplots(figsize=(W, 6.0))
m = major.sort_values("beta_gpt4")
FULL, PARTIAL = {"15", "43"}, {"13", "27"}
for i, r in enumerate(m.itertuples()):
    code = str(r.soc_major).zfill(2)
    if code in FULL:
        ax.barh(i, r.beta_gpt4, color=ORANGE, height=0.74,
                edgecolor=SURFACE, linewidth=1.0, zorder=3)
    elif code in PARTIAL:
        ax.barh(i, r.beta_gpt4, color=SURFACE, height=0.74, edgecolor=ORANGE,
                linewidth=1.1, hatch="/////", zorder=3)
    else:
        ax.barh(i, r.beta_gpt4, color=BLUE, height=0.74,
                edgecolor=SURFACE, linewidth=1.0, zorder=3)
ax.scatter(m.beta_human, np.arange(len(m)), color=INK, s=17, zorder=5,
           label="Human-rated exposure")
for i, r in enumerate(m.itertuples()):
    ax.annotate(f"{r.beta_gpt4:.3f}", (r.beta_gpt4, i), xytext=(5, -3.2),
                textcoords="offset points", fontsize=8.0, color=INK2)
ax.set_yticks(np.arange(len(m)))
ax.set_yticklabels([f"{lab}  ({int(n)})" for lab, n in zip(m.major_label, m.n)])
ax.set_xlabel(r"Mean exposure $\beta = E1 + 0.5\,E2$")
ax.set_xlim(0, 0.92)
ax.grid(axis="y", visible=False)
handles = [Patch(facecolor=ORANGE, edgecolor=SURFACE,
                 label="Wholly in the pathway bundle"),
           Patch(facecolor=SURFACE, edgecolor=ORANGE, hatch="/////",
                 label="Partly in the bundle (13-20xx, 27-30xx)"),
           Patch(facecolor=BLUE, edgecolor=SURFACE, label="Outside the bundle"),
           Line2D([], [], marker="o", ls="", color=INK, ms=5,
                  label="Human-rated exposure")]
ax.legend(handles=handles, frameon=False, loc="lower right", fontsize=8.6)
finish(ax)
fig.savefig(os.path.join(FIGS, "fig2_exposure_by_group.pdf"))
plt.close(fig)

# =============================================================== Figure 3
fig, axes = plt.subplots(1, 2, figsize=(W, 3.6))
ax = axes[0]
ax.plot(jz_all.jobzone, jz_all.beta_gpt4, "-o", color=BLUE, ms=6.5, lw=2.0,
        mec=SURFACE, mew=1.2, zorder=4)
ax.plot(jz_cog.jobzone, jz_cog.beta_gpt4, "-s", color=ORANGE, ms=6.5, lw=2.0,
        mec=SURFACE, mew=1.2, zorder=4)
ax.annotate("All occupations", (4.35, jz_all.beta_gpt4.iloc[3]),
            xytext=(0, 13), textcoords="offset points", ha="center",
            fontsize=8.6, color=BLUE, fontweight="bold")
ax.annotate("Pathway bundle", (4.1, jz_cog.beta_gpt4.iloc[2]),
            xytext=(0, -22), textcoords="offset points", ha="center",
            fontsize=8.6, color=ORANGE, fontweight="bold")
for r in jz_all.itertuples():
    ax.annotate(f"{int(r.n)}", (r.jobzone, r.beta_gpt4), xytext=(0, -14),
                textcoords="offset points", ha="center", fontsize=7.4,
                color=MUTED)
for r in jz_cog.itertuples():
    ax.annotate(f"{int(r.n)}", (r.jobzone, r.beta_gpt4), xytext=(0, 9),
                textcoords="offset points", ha="center", fontsize=7.4,
                color=MUTED)
ax.set_xticks([1, 2, 3, 4, 5])
ax.set_xlim(0.6, 5.4)
ax.set_ylim(0, 0.88)
ax.set_xlabel("O*NET Job Zone (required preparation)")
ax.set_ylabel(r"Mean exposure $\beta$")
panel(ax, "(a) Exposure rises with preparation")
finish(ax)

ax = axes[1]
bins = np.linspace(0, 1, 21)
ax.hist(occ.loc[occ.base, "beta"], bins=bins, color=BLUE, alpha=0.92,
        density=True, zorder=3, label=f"Physical, non-tradable ($n$={int(occ.base.sum())})")
ax.hist(occ.loc[occ.bundle, "beta"], bins=bins, color=ORANGE, alpha=0.72,
        density=True, zorder=4, label=f"Pathway bundle ($n$={int(occ.bundle.sum())})")
for d, c in [(occ.loc[occ.base, "beta"], BLUE), (occ.loc[occ.bundle, "beta"], ORANGE)]:
    ax.axvline(d.mean(), color=c, ls="--", lw=1.4, zorder=5)
ax.annotate("0.172", (occ.loc[occ.base, "beta"].mean(), 3.5), xytext=(4, 0),
            textcoords="offset points", fontsize=8.2, color=BLUE)
ax.annotate("0.656", (occ.loc[occ.bundle, "beta"].mean(), 3.5), xytext=(4, 0),
            textcoords="offset points", fontsize=8.2, color=ORANGE)
ax.set_xlabel(r"Exposure $\beta$")
ax.set_ylabel("Density")
ax.set_ylim(0, 5.2)
ax.legend(frameon=False, fontsize=8.2, loc="upper center")
panel(ax, "(b) Two occupational bundles")
finish(ax)
fig.tight_layout(w_pad=2.0)
fig.savefig(os.path.join(FIGS, "fig3_jobzone_bundles.pdf"))
plt.close(fig)

# =============================================================== Figure 4
ict = wide("BX.GSR.CCIS.CD.MN")
years = list(range(2010, 2025))
bal = ["EGY", "ETH", "KEN", "NGA", "RWA", "TZA", "UGA", "ZAF"]
tot = [sum(ict[c].get(y, np.nan) for c in bal) for y in years]
exza = [sum(ict[c].get(y, np.nan) for c in bal if c != "ZAF") for y in years]

fig, axes = plt.subplots(1, 2, figsize=(W, 3.6))
ax = axes[0]
ax.plot(years, tot, "-o", color=BLUE, ms=5, lw=2.0, mec=SURFACE, mew=1.0, zorder=4)
ax.plot(years, exza, "-s", color=ORANGE, ms=5, lw=2.0, mec=SURFACE, mew=1.0, zorder=4)
ax.axvline(2022.9, color=MUTED, ls=":", lw=1.2, zorder=2)
ax.annotate("ChatGPT, Nov 2022", (2022.6, 4600), xytext=(-6, 0),
            textcoords="offset points", ha="right", fontsize=8.0, color=MUTED)
ax.annotate("Eight economies", (2011.8, 3450), fontsize=8.8,
            color=BLUE, fontweight="bold")
ax.annotate("Excluding South Africa", (2011.8, 900), fontsize=8.8,
            color=ORANGE, fontweight="bold")
ax.set_ylabel("ICT service exports\n(US\\$ million, current)")
ax.set_xlabel("Year")
ax.set_ylim(0, 5400)
ax.set_xlim(2009.4, 2024.6)
ax.set_xticks([2010, 2013, 2016, 2019, 2022, 2024])
panel(ax, "(a) The channel has not contracted")
finish(ax)

ax = axes[1]
vals = [4601e6 / 15000, 19_607_363]
bars = ax.bar([0, 1], vals, color=[ORANGE, BLUE], width=0.52,
              edgecolor=SURFACE, linewidth=1.2, zorder=3)
ax.set_yscale("log")
ax.set_xticks([0, 1])
ax.set_xticklabels(["Jobs supported by\nthe 2024 sector",
                    "Annual entrants,\n2025–2050"], fontsize=9.0)
ax.set_ylabel("Persons (log scale)")
for b, v in zip(bars, vals):
    ax.annotate(f"{v:,.0f}", (b.get_x() + b.get_width() / 2, v),
                xytext=(0, 6), textcoords="offset points", ha="center",
                fontsize=9.4, color=INK, fontweight="bold")
ax.set_ylim(1e5, 3e8)
ax.set_xlim(-0.6, 1.6)
ax.grid(axis="x", visible=False)
ax.annotate("", xy=(0.5, vals[0] * 1.35), xytext=(0.5, vals[1] * 0.74),
            arrowprops=dict(arrowstyle="<->", color=MUTED, lw=1.1))
ax.annotate("64-fold\ngap", (0.5, 2.6e6), ha="center", va="center",
            fontsize=9.0, color=INK2,
            bbox=dict(boxstyle="round,pad=0.3", fc=SURFACE, ec="none"))
panel(ax, "(b) The absorption gap")
finish(ax)
fig.tight_layout(w_pad=2.0)
fig.savefig(os.path.join(FIGS, "fig4_channel_and_gap.pdf"))
plt.close(fig)

# =============================================================== Figure 5
fig, ax = plt.subplots(figsize=(W, 3.9))
e = expo.sort_values("stock_exposure")
y = np.arange(len(e))
ax.hlines(y, e.stock_exposure, e.trajectory_exposure, color=GRID, lw=5, zorder=1)
ax.scatter(e.stock_exposure, y, color=BLUE, s=64, zorder=4, ec=SURFACE, lw=1.2)
ax.scatter(e.trajectory_exposure, y, color=ORANGE, s=64, marker="D", zorder=4,
           ec=SURFACE, lw=1.2)
for i, r in enumerate(e.itertuples()):
    ax.annotate(f"{r.stock_exposure:.3f}", (r.stock_exposure, i),
                xytext=(-7, -3.4), textcoords="offset points", ha="right",
                fontsize=8.0, color=BLUE)
    ax.annotate(f"{r.ratio:.1f}$\\times$", (r.trajectory_exposure, i),
                xytext=(9, -3.4), textcoords="offset points", fontsize=8.4,
                color=ORANGE, fontweight="bold")
ax.set_yticks(y)
ax.set_yticklabels(e.country)
ax.set_xlabel(r"Mean exposure $\beta$")
ax.set_xlim(0.09, 0.80)
ax.set_ylim(-0.7, len(e) - 0.3)
ax.grid(axis="y", visible=False)
ax.legend(handles=[Line2D([], [], marker="o", ls="", color=BLUE, ms=7,
                          label="Stock exposure (current employment)"),
                   Line2D([], [], marker="D", ls="", color=ORANGE, ms=7,
                          label="Trajectory exposure (targeted pathway)")],
          frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.17),
          ncol=2, fontsize=8.8)
finish(ax)
fig.savefig(os.path.join(FIGS, "fig5_stock_vs_trajectory.pdf"))
plt.close(fig)

# =============================================================== Figure 6
m6 = pd.read_csv(os.path.join(DATA, "oli_microwork.txt.gz"), parse_dates=["date"])
nw = m6[m6.status == "new"]
daily = nw.pivot_table(index="date", columns="occupation", values="count",
                       aggfunc="sum")
OCCS = [c for c in daily.columns if c != "Total"]
monthly = daily.resample("MS").mean()
shares = monthly[OCCS].div(monthly["Total"], axis=0) * 100
roll = shares.rolling(12, min_periods=6).mean()

fig, axes = plt.subplots(1, 2, figsize=(W, 3.9),
                         gridspec_kw={"width_ratios": [1.22, 1]})
ax = axes[0]
for o in sorted(OCCS, key=lambda x: -BETA[x]):
    ax.plot(roll.index, roll[o], lw=2.1, color=bcol(BETA[o]), zorder=3,
            solid_capstyle="round")
ax.axvline(pd.Timestamp("2022-11-30"), color=MUTED, ls=":", lw=1.2, zorder=2)
ax.annotate("ChatGPT", (pd.Timestamp("2022-11-30"), 47),
            xytext=(-4, 0), textcoords="offset points", ha="right",
            fontsize=8.0, color=MUTED, rotation=90, va="top")
ax.set_ylim(0, 50)
ax.set_xlim(pd.Timestamp("2016-09-01"), pd.Timestamp("2026-10-01"))
ax.set_ylabel("Share of online vacancies\n(%, twelve-month mean)")
ax.set_xlabel("Year")
last = roll.dropna(how="all").index[-1]
end_labels(ax, {SHORT[o]: (bcol(BETA[o]), roll[o].loc[last]) for o in OCCS}, last)
ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in (2017, 2019, 2021, 2023)])
ax.set_xticklabels(["2017", "2019", "2021", "2023"])
panel(ax, "(a) Demand composition, 2016–2024")
finish(ax)

ax = axes[1]
pre = shares[(shares.index.month <= 8) & (shares.index.year.isin([2021, 2022]))].mean()
post = shares[(shares.index.month <= 8) & (shares.index.year.isin([2023, 2024]))].mean()
chg = (post - pre)[OCCS]
xs = [BETA[o] for o in OCCS]
b = np.polyfit(xs, chg.values, 1)
xx = np.linspace(0.38, 0.79, 20)
ax.plot(xx, np.polyval(b, xx), color=AXIS, ls="--", lw=1.2, zorder=1)
ax.axhline(0, color=AXIS, lw=1.0, zorder=1)
ax.scatter(xs, chg.values, c=[bcol(v) for v in xs], s=95, zorder=4,
           edgecolor=SURFACE, linewidth=1.3)
OFF = {"Creative and multimedia": (9, 1, "left"),
       "Sales and marketing support": (9, 1, "left"),
       "Professional services": (9, 1, "left"),
       "Clerical and data entry": (9, -2, "left"),
       "Microwork": (-9, 3, "right"),
       "Software development and technology": (9, 4, "left"),
       "Writing and translation": (0, -17, "center")}
for o in OCCS:
    dx, dy, ha = OFF[o]
    ax.annotate(SHORT[o], (BETA[o], chg[o]), textcoords="offset points",
                xytext=(dx, dy), ha=ha, fontsize=8.0, color=INK2)
ax.set_xlabel(r"Exposure $\beta$ of the category")
ax.set_ylabel("Change in demand share\n(percentage points)")
ax.set_xlim(0.31, 0.93)
ax.set_ylim(-6.4, 7.2)
ax.text(0.03, 0.05, "Spearman $\\rho = -1.000$\nexact $p = 0.0002$",
        transform=ax.transAxes, fontsize=8.8, color=INK,
        bbox=dict(boxstyle="round,pad=0.35", fc=SURFACE, ec=GRID, lw=0.8))
panel(ax, "(b) Exposure and the shift")
finish(ax)
fig.tight_layout(w_pad=2.6)
fig.savefig(os.path.join(FIGS, "fig6_oli_demand.pdf"))
plt.close(fig)

# =============================================================== Figure 7
ADEQUATE = {"EGY", "KEN", "NGA", "ZAF", "GHA", "ETH"}
fig, axes = plt.subplots(1, 2, figsize=(W, 3.9))
ax = axes[0]
t = ten.sort_values("trajectory_exposure_weighted")
y = np.arange(len(t))
for i, r in enumerate(t.itertuples()):
    adequate = r.iso3 in ADEQUATE
    ax.barh(i, r.trajectory_exposure_weighted,
            color=BLUE if adequate else SURFACE, height=0.72,
            edgecolor=BLUE, linewidth=1.1,
            hatch=None if adequate else "////", zorder=3)
    ax.annotate(f"{r.trajectory_exposure_weighted:.3f}",
                (r.trajectory_exposure_weighted, i), xytext=(5, -3.4),
                textcoords="offset points", fontsize=8.2, color=INK2)
ax.axvline(0.656, color=ORANGE, ls="--", lw=1.6, zorder=5)
ax.annotate("unweighted\nbundle mean", (0.656, -0.42), xytext=(5, 0),
            textcoords="offset points", fontsize=8.0, color=ORANGE, va="bottom")
ax.set_yticks(y)
ax.set_yticklabels(t.country)
ax.set_xlabel(r"Supply-weighted trajectory exposure $\beta$")
ax.set_xlim(0, 0.88)
ax.set_ylim(-0.75, len(t) - 0.25)
ax.grid(axis="y", visible=False)
ax.legend(handles=[Patch(facecolor=BLUE, edgecolor=BLUE, label="adequate sample"),
                   Patch(facecolor=SURFACE, edgecolor=BLUE, hatch="////",
                         label="fewer than 20,000 profiles")],
          frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22),
          ncol=2, fontsize=8.2)
panel(ax, "(a) Weighted by each online workforce")
finish(ax)

ax = axes[1]
cols = [c for c in mix.columns if c != "portfolio_exposure"]
for o in sorted(cols, key=lambda x: -BETA[x]):
    ax.plot(mix.index, mix[o], lw=2.1, color=bcol(BETA[o]), marker="o",
            ms=3.6, mec=SURFACE, mew=0.8, zorder=3)
ax.set_xlabel("Year")
ax.set_ylabel("Share of African online workers (%)")
ax.set_ylim(0, 56)
ax.set_xlim(2016.7, 2030.6)
ax.set_xticks([2017, 2020, 2023])
end_labels(ax, {SHORT[o]: (bcol(BETA[o]), mix[o].iloc[-1]) for o in cols},
           mix.index[-1])
panel(ax, "(b) African supply, reallocating")
finish(ax)
fig.tight_layout(w_pad=2.6)
fig.savefig(os.path.join(FIGS, "fig7_oli_supply.pdf"))
plt.close(fig)

print("all figures written")
for f in sorted(os.listdir(FIGS)):
    if f.endswith(".pdf"):
        print("  ", f, f"{os.path.getsize(os.path.join(FIGS,f))//1024} KB")
