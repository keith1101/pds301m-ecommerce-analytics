# Issue #22 — final integrated notebook handoff

Notebook: `notebooks/06_final_integrated_analysis.ipynb` (executed outputs included).

To reproduce: `python -m pip install -r requirements.txt`; `jupyter notebook`; restart kernel and run all from notebooks directory. Input CSVs are already included in the complete handoff. Primary sources: `src/eda.py`, `src/feature_engineering.py`, `src/anomaly_detector.py`, `src/reconcile.py`, `src/scraper.py`. No business logic was copied to a competing module. CSV reconciliation is performed with `pathlib`-based file locations.

Verification performed: notebook Run All completed without errors; all available KPI #18 equality checks passed; saved RFM verified against recomputation; scraping evidence: 1,000 titles validated; four generated figures; `pytest`: 41 passed.

**Review limitation:** `data/processed/cancelled_retail.csv` was not supplied. Cancelled invoice count (9,251) is stated in Issue #18 but cannot be independently reverified from the supplied data. To meet the optional reconciliation audit too, add this artifact or regenerate it through `RetailDataProcessor` using raw Excel.

Other caveats: Books to Scrape 50-page traversal is evidenced by `src/scraper.py` and 1,000-row saved CSV, not a live scrape. `src/eda.py` and `src/reconcile.py` standalone main entrypoints still contain Windows-only string path concatenation; final notebook bypasses these entrypoints and calls their reusable analysis functions with `pathlib` paths. No claims of merging a PR or Huy's review are made.
