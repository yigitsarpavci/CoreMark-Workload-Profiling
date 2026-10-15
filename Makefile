# ==============================================================================
# CoreMark Workload Profiling Makefile
# ==============================================================================

PYTHON ?= python3

.PHONY: all benchmark clean build-report help

all: benchmark

help:
	@echo "Available targets:"
	@echo "  make benchmark    - Run the automated 8-configuration CoreMark suite"
	@echo "  make build-report - Compile report.tex with pdflatex"
	@echo "  make clean        - Clean build artifacts in coremark and report"

benchmark:
	$(PYTHON) scripts/run_benchmarks.py

build-report:
	cd report && pdflatex -interaction=nonstopmode report.tex && pdflatex -interaction=nonstopmode report.tex

clean:
	$(MAKE) -C coremark clean
	rm -f report/*.aux report/*.log report/*.out report/*.synctex.gz report/*.toc
