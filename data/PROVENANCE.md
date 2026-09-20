# Provenance of every file in this directory

Licences and required attributions are in `../DATA-LICENCES.md`. This file
records where each file came from, what was done to it, and what was checked.

| File | Origin | Transformation |
|---|---|---|
| `occ_level.csv` | `openai/GPTs-are-GPTs`, `data/occ_level.csv` | none, byte-identical to the source |
| `onet_jobzones.csv` | O*NET 29.1 `Job Zones.txt` | tab-separated converted to CSV; the two columns kept are `onetsoc` and `jobzone`; values unchanged |
| `oli_microwork.txt.gz` | figshare 10.6084/m9.figshare.3761562, `OLI_microwork_data_2024-08-22.txt` | gzip only |
| `worker_countrydata_2024-09-02.txt.gz` | same deposit, `worker_countrydata_2024-09-02.txt` | gzip only |
| `countries_regions.txt` | same deposit, `Countries_continents_regions.txt` | none |
| `oli11data.txt` | same deposit, `OLI11data_2024-09-02.txt` | none. Covers the Spanish, Russian and Philippine platform domains only and is **not used** in the analysis; included for completeness |
| `oli_worker_codebook.txt` | same deposit | none |
| `wdi_raw_0*.csv` | World Bank WDI API | see below |
| `popprojAge1dt.rda`, `popAge1dt.rda` | fetched by `../scripts/fetch_wpp.py` | not redistributed |

---

## The World Development Indicators panel

The WDI files were assembled from `https://api.worldbank.org/v2` on
20 September 2026 and stored in long format with columns
`indicator,iso3,year,value`. Three points of detail matter for anyone checking
the numbers.

**Units of the ICT service export series.** The World Bank reports
`BX.GSR.CCIS.CD` in current US dollars. It is stored here under the local key
`BX.GSR.CCIS.CD.MN` in **millions** of current US dollars. The conversion was
verified against the raw JSON for Kenya, Ethiopia and Rwanda over 2020 to 2024,
digit for digit: Kenya 2024 is 853,401,195.56 dollars, stored as 853.40;
Ethiopia 2024 is 42,591,405.05, stored as 42.59; Rwanda 2024 is 34,451,932.61,
stored as 34.45. Egypt required particular care because its values were
returned on a different scale in a first retrieval, and the stored series was
rebuilt from the exact JSON.

**Rounding.** Values are stored at the precision retrieved, except where noted
in the file header comments, where they were rounded to three decimal places.
Rounding was applied after retrieval and never before a verification check.

**Coverage.** Not every country reports every indicator in every year. Missing
observations are absent from the file rather than recorded as zero, and the
analysis scripts drop them rather than imputing.

---

## A note on how this panel was retrieved

The panel was assembled in an environment whose network policy blocked direct
access to the World Bank, ILOSTAT and United Nations data portals, so the WDI
series were retrieved through a web-fetch channel and transcribed rather than
downloaded as bulk files. Three safeguards were applied: values for a subset of
countries and years were re-retrieved independently and compared digit for
digit; a unit inconsistency in the ICT service export series was caught by that
comparison and corrected; and every figure quoted in the manuscript is checked
programmatically against the computed output rather than typed by hand.

Anyone re-running this work from a network without those restrictions should
re-pull the panel directly from the WDI API using the indicator codes listed in
`../DATA-LICENCES.md` and re-run `src/01_core_analysis.py`. The results in
`results/` should reproduce exactly. If they do not, the panel in this
directory is the thing to suspect, not the code.
