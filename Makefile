PY ?= python3

.PHONY: all data analysis figures clean

all: analysis figures

data:
	$(PY) scripts/fetch_wpp.py

analysis: data
	$(PY) src/01_core_analysis.py
	$(PY) src/02_supplementary.py
	$(PY) src/03_oli_demand.py
	$(PY) src/04_oli_workers.py
	$(PY) src/05_robustness.py

figures:
	$(PY) src/06_figures.py

clean:
	rm -f results/*.txt results/*.csv figures/*.pdf
