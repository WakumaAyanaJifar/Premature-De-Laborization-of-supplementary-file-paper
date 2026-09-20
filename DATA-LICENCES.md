# Data sources, licences and required attributions

Every input to this analysis is public. This file records what each source is,
under what terms it is redistributed here, and the attribution the licence
requires. Licence text was checked against the source on 21 September 2026.

---

## 1. Occupational exposure ratings

**File:** `data/occ_level.csv`
**Source:** replication repository accompanying Eloundou, T., Manning, S.,
Mishkin, P., & Rock, D. (2024). GPTs are GPTs: Labor market impact potential of
LLMs. *Science*, 384(6702), 1306--1308.
Repository: `https://github.com/openai/GPTs-are-GPTs`, file `data/occ_level.csv`.
**Licence:** MIT Licence, Copyright (c) 2024 OpenAI. Redistribution is permitted
with the copyright and permission notice, reproduced in `LICENSE-MIT-OpenAI.txt`.
**Retrieved:** 20 September 2026.

Columns used: `dv_rating_alpha`, `dv_rating_beta`, `dv_rating_gamma`,
`human_rating_beta`, where alpha = E1, beta = E1 + 0.5·E2 and gamma = E1 + E2.

## 2. O*NET Job Zones

**File:** `data/onet_jobzones.csv`
**Source:** O*NET 29.1 Database, `Job Zones.txt`, National Center for O*NET
Development, United States Department of Labor, Employment and Training
Administration. `https://www.onetcenter.org/database.html`
**Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0).
**Required attribution:** "This site incorporates information from the O*NET
Database by the U.S. Department of Labor, Employment and Training
Administration (USDOL/ETA). Used under the CC BY 4.0 licence. O*NET is a
trademark of USDOL/ETA."
**Retrieved:** 20 September 2026. Reformatted from tab-separated to CSV; values
unchanged.

## 3. Online Labour Index

**Files:** `data/oli_microwork.txt.gz` (demand series),
`data/worker_countrydata_2024-09-02.txt.gz` (worker supplement),
`data/countries_regions.txt` (country to region map),
`data/oli11data.txt` (non-English domain supplement, not used in the analysis),
`data/oli_worker_codebook.txt`.
**Source:** Kässi, O., Hadley, C., & Lehdonvirta, V. Online Labour Index:
Measuring the Online Gig Economy for Policy and Research. figshare dataset.
`https://doi.org/10.6084/m9.figshare.3761562`. Files as deposited on
2 September 2024.
**Licence:** CC BY 4.0.
**Required citation, as given by the depositors:** Kässi, Otto; Hadley,
Charlie; Lehdonvirta, Vili (2019). Online Labour Index: Measuring the Online
Gig Economy for Policy and Research. figshare. Dataset.
`https://doi.org/10.6084/m9.figshare.3761562.v3042`
**Accompanying paper:** Kässi, O., & Lehdonvirta, V. (2018). Online labour
index: Measuring the online gig economy for policy and research.
*Technological Forecasting and Social Change*, 137, 241--248.
**Retrieved:** 20 September 2026. Compressed with gzip; contents unchanged.

**Constraint stated by the producers and observed here:** the worker supplement
supports relative shares only. Conclusions about the increase or decrease in
labour supply over time are, in the codebook's words, suspect. All quantities
computed from it in this repository are shares or share-weighted means.

## 4. World Development Indicators

**Files:** `data/wdi_raw_01.csv` to `data/wdi_raw_05.csv`
**Source:** World Bank, World Development Indicators, via
`https://api.worldbank.org/v2`.
**Licence:** CC BY 4.0, under the World Bank's Terms of Use for Datasets.
**Retrieved:** 20 September 2026.

Indicators: `NV.IND.MANF.ZS`, `NY.GDP.PCAP.PP.KD`, `SL.IND.EMPL.ZS`,
`SL.SRV.EMPL.ZS`, `SL.AGR.EMPL.ZS`, `SL.UEM.1524.ZS`, `SL.TLF.TOTL.IN`,
`BX.GSR.CCIS.CD`. Employment shares are modelled International Labour
Organization estimates. ICT service exports are stored in millions of current
US dollars under the local key `BX.GSR.CCIS.CD.MN`; see
`data/PROVENANCE.md` for the unit conversion and the verification performed on
it.

## 5. United Nations World Population Prospects 2024

**Files:** not redistributed. `scripts/fetch_wpp.py` downloads
`popprojAge1dt.rda` and `popAge1dt.rda` from the `wpp2024` R data package
maintained by the United Nations Population Division
(`https://github.com/PPgp/wpp2024`, files under `data/`).
**Source:** United Nations, Department of Economic and Social Affairs,
Population Division (2024). *World Population Prospects 2024*, medium variant,
single-year age projections.
**Licence:** the `wpp2024` package ships its own LICENSE file; consult it and
the United Nations terms of use before redistributing. We therefore fetch
rather than redistribute these files.

---

## Note on redistribution

Including a file here does not relicense it. Each data file remains under the
licence of its original source as recorded above. Code in `src/` and `scripts/`
is MIT licensed and is the only part of this repository to which the root
`LICENSE` applies.
