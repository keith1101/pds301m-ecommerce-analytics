# Issue #5 — RFM Methodology & Prototype

## 1. Purpose

Build a reproducible customer-segmentation baseline using Recency, Frequency and Monetary (RFM), including explicit eligibility rules, tie-safe scoring, segment thresholds, a Pandas prototype, tests, and a production-ready `customer_segments.csv` path.

## 2. RFM population

A transaction row is eligible for RFM only when all rules below are true:

1. `InvoiceNo` does **not** start with `C` (cancelled invoice).
2. `CustomerID` is present.
3. `CustomerID` is not the anonymous placeholder `Guest` used by the current `cleaned_retail.csv`.
4. `Quantity > 0`.
5. `UnitPrice > 0`.
6. `InvoiceDate` is parseable.
7. Exact duplicate rows are removed before aggregation.

`Revenue` is recalculated as:

```text
Revenue = Quantity × UnitPrice
```

Why exclude `Guest`: anonymous transactions cannot be linked to one real customer. Treating every anonymous row as one customer would create a synthetic high-frequency/high-monetary customer and distort segmentation.

## 3. Reference date and RFM formulas

The reference date is derived from the final **valid identified-customer purchase**:

```text
ReferenceDate = normalize(max(valid InvoiceDate)) + 1 day
```

This makes a purchase on the final transaction date have `Recency = 1`, not 0, and the same rule is used in prototype and production.

Per `CustomerID`:

```text
Recency   = (ReferenceDate - LastPurchaseDate) in calendar days
Frequency = count of distinct valid InvoiceNo
Monetary  = sum(Quantity × UnitPrice)
```

Frequency deliberately uses `nunique(InvoiceNo)`: multiple product lines on the same invoice count as one purchase.

## 4. RFM scoring (1–5)

Direction:

- Lower Recency is better → higher R score.
- Higher Frequency is better → higher F score.
- Higher Monetary is better → higher M score.

### Primary method: quintile thresholds

For each metric, compute empirical q20/q40/q60/q80 cutoffs. If all four cutoffs are distinct, assign raw buckets 1–5 by threshold. Values exactly equal to a cutoff remain together in the same bucket, so tied raw values are never split.

For Recency, the raw quintile bucket is inverted (`score = 6 - bucket`) because lower Recency is better.

### Tie / low-cardinality fallback

Direct `pd.qcut(..., 5)` can fail when quantile edges are duplicated or when too few distinct values exist. The prototype therefore falls back to **dense unique-value scaling**:

- equal raw values always receive equal scores;
- one unique value receives neutral score 3;
- 2–4 unique values are spread deterministically across the 1–5 scale;
- no duplicate-bin error is possible.

This prioritizes deterministic labels and tie consistency over forcing exactly 20% of customers into every bucket.

## 5. Segment rules and precedence

Rules are evaluated top-to-bottom; first match wins. Therefore every customer receives exactly one segment.

| Priority | Segment | Rule |
|---:|---|---|
| 1 | Champions | `R >= 4 and F >= 4 and M >= 4` |
| 2 | Loyal Customers | `R >= 3 and F >= 4` |
| 3 | At Risk | `R <= 2 and (F >= 3 or M >= 3)` |
| 4 | Potential Loyalists | `R >= 4 and 2 <= F <= 3` |
| 5 | New Customers | `R >= 4 and F == 1` |
| 6 | Hibernating | `R <= 2 and F <= 2 and M <= 2` |
| 7 | Others | all remaining score combinations |

These are project baseline thresholds for Issue #5. If the team later changes segment definitions or compares them with K-Means, that change should be versioned because customer counts will change.

## 6. `customer_segments.csv` schema

| Column | Meaning |
|---|---|
| `CustomerID` | identified customer key |
| `Recency` | days since last valid purchase |
| `Frequency` | distinct valid invoices |
| `Monetary` | total valid purchase value |
| `R_score` | Recency score 1–5 |
| `F_score` | Frequency score 1–5 |
| `M_score` | Monetary score 1–5 |
| `RFM_score` | three-digit code such as `545` |
| `RFM_total` | R + F + M, range 3–15 |
| `Segment` | rule-based segment label |
| `LastPurchaseDate` | customer most recent valid purchase date |
| `ReferenceDate` | run-level RFM reference date |

## 7. Prototype validation cases

Automated tests cover:

- one-order customers;
- multiple orders per customer;
- multiple product lines on one invoice;
- cancelled invoices;
- missing `CustomerID`;
- the `Guest` anonymous placeholder;
- non-positive quantity/price;
- exact duplicates;
- equal RFM values;
- low-cardinality/duplicate-quantile scoring;
- reference-date correctness;
- score range 1–5 and segment precedence.

## 8. Current production run on `cleaned_retail.csv`

The supplied processed dataset contains **524,878 rows**. The current cleaning pipeline has no remaining cancelled rows, missing IDs, non-positive quantity/price rows, invalid dates, or exact duplicates. It does contain **132,186 rows labelled `Guest`**, which are intentionally excluded from customer-level RFM because they represent anonymous purchases rather than one identifiable customer.

After the RFM population rule is applied:

- valid identified-customer transaction rows: **392,692**
- distinct identified customers: **4,338**
- distinct valid invoices: **18,532**
- latest valid identified-customer purchase: **2011-12-09 12:50:00**
- RFM reference date: **2011-12-10**


### Current score thresholds

All three metrics use the primary quantile method on the current production run because q20/q40/q60/q80 are distinct.

| Metric | q20 | q40 | q60 | q80 | Interpretation |
|---|---:|---:|---:|---:|---|
| Recency (days) | 13.8 | 33 | 72 | 180 | `R=5` for <=13.8 days; `R=1` for >180 days |
| Frequency (invoices) | 1 | 2 | 3 | 6 | `F=1` for <=1 invoice; `F=5` for >6 invoices |
| Monetary | 249.344 | 487.412 | 933.348 | 2055.05 | `M=1` for <=249.344; `M=5` for >2055.05 |

These are **data-dependent run thresholds**, not hard-coded constants. A new official dataset recomputes them using the same methodology.


### Segment counts

| Segment | Customers | Share |
|---|---:|---:|
| Hibernating | 954 | 21.99% |
| Champions | 911 | 21.00% |
| At Risk | 773 | 17.82% |
| Others | 599 | 13.81% |
| Potential Loyalists | 484 | 11.16% |
| Loyal Customers | 381 | 8.78% |
| New Customers | 236 | 5.44% |

Total: **4,338 customers**.


## 9. Repository integration

Recommended Issue #5 artifacts:

```text
docs/rfm_methodology.md
src/feature_engineering.py
notebooks/04_customer_segmentation.ipynb
tests/test_rfm.py
data/processed/customer_segments.csv
```

`src/feature_engineering.py` contains reusable production logic. The notebook demonstrates the method and validates the actual processed dataset instead of being the only place where business logic exists.
