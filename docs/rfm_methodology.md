# Issue #5 — RFM Methodology & Prototype

## 1. Purpose

Build a reproducible RFM customer-segmentation baseline for Issue #5 by:

- defining Recency, Frequency and Monetary consistently;
- defining a common reference-date rule;
- defining tie-safe R/F/M scoring from 1–5;
- defining rule-based customer segments and their precedence;
- designing the future `customer_segments.csv` schema;
- validating the methodology with a Pandas prototype and edge-case tests;
- preparing reusable code that can later run on `cleaned_retail.csv`.

Issue #5 does **not** require the official full-data analysis or exporting the production `customer_segments.csv`.

## 2. RFM population

A transaction row is eligible for RFM only when all rules below are true:

1. `InvoiceNo` is present and non-empty.
2. `InvoiceNo` does **not** start with `C` (cancelled invoice).
3. `CustomerID` is present.
4. `CustomerID` is not an anonymous placeholder such as `Guest`.
5. `Quantity > 0`.
6. `UnitPrice > 0`.
7. `InvoiceDate` is parseable.

Exact duplicate handling belongs to the upstream cleaning pipeline. The RFM layer audits duplicates but does **not** call `drop_duplicates()` or apply an independent deduplication key. This prevents Issue #5 from silently changing the cleaned-data contract.

`Revenue` is recalculated as:

```text
Revenue = Quantity × UnitPrice
```

Anonymous rows are excluded from customer-level RFM because they cannot be linked to one real customer. Treating all anonymous purchases as one customer would create a synthetic high-frequency/high-monetary customer and distort segmentation.

## 3. Reference date and RFM formulas

The reference date is derived from the final **valid identified-customer purchase**:

```text
ReferenceDate = normalize(max(valid InvoiceDate)) + 1 day
```

Using the next calendar day makes a customer purchasing on the final transaction date have `Recency = 1`, not 0. The same rule must be used in prototype and later official analysis.

Per `CustomerID`:

```text
LastPurchaseDate = max(valid InvoiceDate)
Recency          = (ReferenceDate - LastPurchaseDate) in calendar days
Frequency        = count of distinct valid InvoiceNo
Monetary         = sum(Quantity × UnitPrice)
```

Frequency deliberately uses `nunique(InvoiceNo)`: multiple product lines on the same invoice count as one purchase.

## 4. RFM scoring (1–5)

### 4.1 Direction

- Lower Recency is better → higher `R_score`.
- Higher Frequency is better → higher `F_score`.
- Higher Monetary is better → higher `M_score`.

### 4.2 Percentile-rank scoring

Direct `pd.qcut(..., 5)` may fail or become unstable when many customers share the same raw value or when fewer than five distinct values exist.

Issue #5 therefore uses **average percentile ranks**:

```python
percentile_rank = metric.rank(
    method="average",
    pct=True,
    ascending=True,
)
```

The raw percentile rank is mapped to five score levels:

```text
F_score = ceil(percentile_rank(Frequency) × 5)
M_score = ceil(percentile_rank(Monetary) × 5)
```

Recency has the opposite direction, so its score is reversed:

```text
R_score = 6 - ceil(percentile_rank(Recency) × 5)
```

All scores are clipped to `[1, 5]`.

### 4.3 Tie and low-cardinality behavior

`method="average"` is intentional:

- equal raw values receive the same average percentile rank;
- equal raw values therefore receive the same R/F/M score;
- the method works even when there are fewer than five distinct values;
- no duplicate quantile-bin error occurs;
- score groups are **not required** to contain exactly 20% of customers when ties exist.

The prototype prioritizes deterministic treatment of equal values over forcing equal-sized buckets.

Example:

```text
Frequency raw:   1  1  1  2  2  3
Percentile rank: .333 .333 .333 .75 .75 1.0
F_score:         2  2  2  4  4  5
```

If every customer has the same raw value, all customers receive the same score because their average percentile ranks are equal.

## 5. Segment rules and precedence

Rules are evaluated top-to-bottom; the **first matching rule wins**. Therefore each customer receives exactly one segment.

| Priority | Segment | Rule |
|---:|---|---|
| 1 | Champions | `R >= 4 and F >= 4 and M >= 4` |
| 2 | Loyal Customers | `R >= 3 and F >= 4` |
| 3 | At Risk | `R <= 2 and (F >= 3 or M >= 3)` |
| 4 | Potential Loyalists | `R >= 4 and 2 <= F <= 3` |
| 5 | Hibernating | `R <= 2 and F <= 2 and M <= 2` |
| 6 | Others | all remaining score combinations |

The baseline deliberately does not infer customer tenure or first-purchase status from RFM. Recency describes how recently a customer purchased, not when the customer relationship started; tenure-based segmentation would require an additional first-purchase definition.

These thresholds are the rule-based baseline for Issue #5. If the team later changes segment definitions or compares them with K-Means, the change should be versioned because segment counts will change.

## 6. Designed `customer_segments.csv` schema

Issue #5 requires the **design** of the future `customer_segments.csv` structure. It does not require exporting the official production CSV.

### 6.1 Row granularity

Each row represents **one unique customer**:

```text
valid transaction rows
        ↓
group by CustomerID
        ↓
1 CustomerID = 1 row
```

`CustomerID` is the logical primary key and must be unique and non-null.

### 6.2 Column specification

| Column | Data type | Required | Meaning |
|---|---|---:|---|
| `CustomerID` | string | Yes | Identified customer key |
| `Recency` | integer | Yes | Days from `LastPurchaseDate` to `ReferenceDate` |
| `Frequency` | integer | Yes | Number of distinct valid invoices |
| `Monetary` | float | Yes | Total valid purchase value |
| `R_score` | integer | Yes | Recency score in `[1, 5]` |
| `F_score` | integer | Yes | Frequency score in `[1, 5]` |
| `M_score` | integer | Yes | Monetary score in `[1, 5]` |
| `RFM_score` | string | Yes | Three-character R/F/M code, e.g. `545` |
| `RFM_total` | integer | Yes | `R + F + M`, range `[3, 15]` |
| `Segment` | string | Yes | Rule-based segment label |
| `LastPurchaseDate` | date | Yes | Most recent valid purchase date |
| `ReferenceDate` | date | Yes | Common run-level reference date |

Agreed column order:

```text
CustomerID
Recency
Frequency
Monetary
R_score
F_score
M_score
RFM_score
RFM_total
Segment
LastPurchaseDate
ReferenceDate
```

Equivalent future CSV header:

```csv
CustomerID,Recency,Frequency,Monetary,R_score,F_score,M_score,RFM_score,RFM_total,Segment,LastPurchaseDate,ReferenceDate
```

### 6.3 Schema constraints

The prototype output should satisfy:

- `CustomerID` is unique and non-null;
- anonymous customer identifiers are excluded;
- `Recency >= 1`;
- `Frequency >= 1`;
- `Monetary > 0`;
- `R_score`, `F_score`, `M_score` are integers in `[1, 5]`;
- `RFM_score` is exactly three score digits;
- `RFM_total` is in `[3, 15]`;
- each customer has exactly one `Segment`;
- `LastPurchaseDate <= ReferenceDate`;
- all customers in one RFM run use the same `ReferenceDate`.

Allowed segment labels:

```text
Champions
Loyal Customers
At Risk
Potential Loyalists
Hibernating
Others
```

## 7. Prototype validation cases

The prototype and automated tests cover:

- one-order customers;
- multiple orders per customer;
- multiple product lines on one invoice;
- cancelled invoices;
- missing/blank `InvoiceNo`;
- missing `CustomerID`;
- anonymous `Guest`;
- non-positive quantity/price;
- exact duplicates are audited and left untouched by the RFM layer;
- equal RFM values;
- low-cardinality percentile-rank scoring;
- reference-date correctness;
- score range 1–5;
- segment precedence;
- designed `customer_segments.csv` schema.

## 8. Readiness for `cleaned_retail.csv`

Issue #5 only requires reusable code to be ready for the later official dataset.

Intended later usage:

```python
cleaned = pd.read_csv("data/processed/cleaned_retail.csv")
customer_segments = calculate_rfm(cleaned)
```

Issue #5 does **not** execute the official full-data segmentation and does **not** call:

```python
customer_segments.to_csv(...)
```

Exporting the official `customer_segments.csv` belongs to a later analysis/integration step.

## 9. Repository integration

Issue #5 artifacts:

```text
docs/rfm_methodology.md
src/feature_engineering.py
notebooks/04_customer_segmentation.ipynb
tests/test_rfm.py
```

Responsibilities:

- `docs/rfm_methodology.md`: methodology, scoring, segment thresholds and schema design;
- `src/feature_engineering.py`: reusable Pandas RFM implementation;
- `notebooks/04_customer_segmentation.ipynb`: deterministic prototype and validation;
- `tests/test_rfm.py`: automated edge-case regression tests.

`data/processed/customer_segments.csv` is deliberately **not** an Issue #5 deliverable.
