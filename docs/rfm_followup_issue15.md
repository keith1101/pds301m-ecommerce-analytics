# Issue #15 — RFM Follow-up & Data Integration

## Scope

This follow-up stabilizes RFM methodology and repository integration before Issue #8. It does not export the production `customer_segments.csv` and does not perform full-data segment analysis.

## Decisions locked by Issue #15

1. **New Customers**: not part of the six-label RFM baseline. Neither `Frequency == 1` nor a score-only rule proves customer tenure.
2. **Scoring ties**: `rank(method="average", pct=True)` remains the standard; equal raw values receive equal scores.
3. **Constant metric**: when all values of one R/F/M metric are equal, every observation receives neutral score `3`.
4. **Guest/anonymous**: anonymous labels such as `Guest` are excluded case-insensitively before customer grouping.
5. **InvoiceNo**: missing/blank invoices are ineligible; cancelled invoices beginning with `C` are ineligible.
6. **Duplicates**: deduplication is owned by the upstream cleaning pipeline. RFM audits exact duplicates but does not call `drop_duplicates()`.
7. **Quantity/UnitPrice audit**: missing/blank, non-numeric and non-positive numeric values are reported as separate categories.
8. **Schema**: `CUSTOMER_SEGMENTS_COLUMNS` is imported from `src.feature_engineering`; notebook/tests must not redefine the production schema.
9. **Dataset location**: full-data Issue #8 expects `data/processed/cleaned_retail.csv`; the notebook does not auto-download the UCI dataset.

## Verification

From repository root:

```bash
pytest -q
python -m pytest -q
```

Execute the notebook from a fresh kernel/environment:

```bash
python -m jupyter nbconvert \
  --to notebook \
  --execute notebooks/04_customer_segmentation.ipynb \
  --output 04_customer_segmentation_executed.ipynb
```

For a repository containing the real processed dataset, run an integration smoke check only; do not export `customer_segments.csv` as part of Issue #15.

## Issue #8 handoff

Issue #8 receives a fixed methodology contract: identified customers only, distinct valid invoices for Frequency, valid purchase revenue for Monetary, next-day reference date, tie-safe 1–5 scoring with neutral constant-metric handling, and exactly these six labels: Champions, Loyal Customers, At Risk, Potential Loyalists, Hibernating, Others.

## Dependency / branch note

Issue #15 depends on #5, #14 and #16. Before merge, the Issue #15 branch must be synchronized with the latest `develop` containing #14/#16 and the full test/notebook verification must be repeated. This archive has no Git history, so branch synchronization itself must be performed in the actual repository.
