# Evidence QA Notes

- Source: Reconciled dataset, `data/processed/cleaned_retail.csv`.
- Detection: existing `src.anomaly_detector.OrderAnomalyDetector.detect_iqr_anomalies()`, not a rewritten rule.
- Order population: 19,960 distinct invoices; revenue flags 1,811; quantity flags 1,445; union 2,185.
- IQR bounds: Revenue £1,006.11375; Quantity 636.5 units.
- Total valid sales Revenue: £10,642,110.804 (round to £10,642,110.80).
- Combined flagged Revenue: £5,345,163.731 (50.2265371% of total).
- Revenue-only flags' Revenue: £5,089,007.771.
- Quantity-only flagged invoices: 374; Revenue: £256,155.96.
- Cancellation input independently checked: 9,251 rows, 3,836 unique cancellation invoices, 275,560 absolute returned units. Note: 9,251 is a row count, not a distinct-invoice count.
- Reproduce with: `python -c "from src.anomaly_detector import OrderAnomalyDetector; d=OrderAnomalyDetector(cleaned_data_path='data/processed/cleaned_retail.csv',cancelled_data_path='data/processed/cancelled_retail.csv'); a=d.detect_iqr_anomalies(); print(a.loc[a.IsAnomaly,'Revenue'].sum(), a.loc[a.IsAnomaly,'Revenue'].sum()/a.Revenue.sum())"` from repository root.
