PYTHON := python3

.PHONY: all run loop clean

all: run

# single collection cycle
run:
	$(PYTHON) process.py

# continuous loop with auto-commit (reads interval from config.ini)
loop:
	bash autocommit.sh

clean:
	rm -f data/*.csv
	find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
