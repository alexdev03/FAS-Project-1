PYTHON  := .venv/bin/python
COLLECT_OUT := data/collect_latest.csv
LOGS_OUT    := data/logs_latest.csv
DB          := data/metrics.db

.PHONY: all setup collect analyze report dashboard autocommit loop clean

all: collect analyze report

# ---- Setup ---------------------------------------------------------------
setup:
	bash setup.sh

# ---- Raccolta dati -------------------------------------------------------
collect: data/
	@echo "[collect] Raccogliendo metriche di sistema..."
	bash collect/collect.sh >> $(COLLECT_OUT)
	@echo "[collect] Analizzando log di sistema..."
	bash collect/parse_logs.sh > $(LOGS_OUT)
	$(PYTHON) analyze/store.py \
		--db $(DB) \
		--metrics $(COLLECT_OUT) \
		--logs $(LOGS_OUT)

# ---- Analisi -------------------------------------------------------------
analyze:
	$(PYTHON) analyze/analyze.py --db $(DB) --metric cpu_pct
	$(PYTHON) analyze/analyze.py --db $(DB) --metric mem_used_mb
	$(PYTHON) analyze/analyze.py --db $(DB) --metric cpu_pct --anomaly

# ---- Report grafici ------------------------------------------------------
report: reports/
	$(PYTHON) analyze/report.py --db $(DB) --out reports/

# ---- Dashboard web -------------------------------------------------------
dashboard:
	$(PYTHON) dashboard/app.py

# ---- Raccolta automatica + push ------------------------------------------
autocommit:
	bash collect/autocommit.sh

loop:
	bash collect/autocommit.sh --loop

# ---- Utility -------------------------------------------------------------
data/:
	mkdir -p data

reports/:
	mkdir -p reports

clean:
	rm -f $(DB) $(COLLECT_OUT) $(LOGS_OUT)
	rm -f reports/*.png
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "[clean] Fatto."
