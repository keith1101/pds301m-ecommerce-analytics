## Summary

Closes #5

Implements the RFM methodology and prototype for customer segmentation.

### Changes
- documents RFM population, formulas, reference-date rule, scoring and segment thresholds;
- adds reusable Pandas RFM functions in `src/feature_engineering.py`;
- adds tie-safe quantile scoring with deterministic low-cardinality fallback;
- excludes anonymous `Guest` transactions from customer-level RFM;
- adds prototype/production notebook and exports `customer_segments.csv`;
- adds automated tests for cancellations, missing IDs, invalid values, multi-line invoices, duplicates, ties and reference date.

### Test
```bash
pytest -q tests/test_rfm.py
```

Run `notebooks/04_customer_segmentation.ipynb` from top to bottom with `data/processed/cleaned_retail.csv` available.
