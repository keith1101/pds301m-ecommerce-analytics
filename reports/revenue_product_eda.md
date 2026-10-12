# Revenue & Product EDA

## 1. Analysis questions
Which customer/product groups generate the most revenue? How does revenue trend over time?
(P4 topic: customer and product analysis in online retail)

## 2. Data
- Source: `data/processed/cleaned_retail.csv`, produced by the cleaning pipeline
- Scope: 524,878 valid sales transactions, 12/2010–12/2011, UK-based online gift store
- Population: cancelled invoices excluded (InvoiceNo starting with C), Quantity and UnitPrice > 0, deduplicated; Guest (anonymous) rows kept
- Definition: Revenue = Quantity × UnitPrice

## 3. Results

### 3.1 Total revenue

| Metric | Value |
|---|---:|
| Valid transaction rows | 524,878 |
| Total Revenue | £10,642,110.80 |
| Non-Guest Revenue | £8,887,208.89 |
| Guest Revenue | £1,754,901.91 |

Consistency checks:

- `Revenue = Quantity × UnitPrice` recomputed independently and matches the `Revenue` column.
- Non-Guest Revenue matches the population used for RFM.
- Guest rows stay in total Revenue but are excluded from RFM.
- Cancelled invoices are separated into `cancelled_retail.csv` and are not part of the sales revenue population.

### 3.2 Monthly revenue trend

Notable points:

- Revenue peaks in **11/2011** at about **£1.5M**.
- Revenue is clearly lower in **02/2011** and **04/2011**, about **£0.52M**.
- Revenue rises strongly from around September to November 2011.
- `12/2010` and `12/2011` are partial months, so they should not be compared directly with full months.

Chart:

`charts/revenue_monthly_line.png`

### 3.3 Revenue by country
- United Kingdom: **84.6%** (~£9.0M). The business depends almost entirely on the UK domestic market.
- The next 9 countries (Netherlands, EIRE, Germany, France, Australia, Spain, Switzerland, Belgium, Sweden) combined account for only ~15%.

### 3.4 Top products

Service codes and accounting entries that do not represent physical products are excluded from the product ranking but kept in total revenue:

| StockCode | Description / Meaning | Treatment |
|---|---|---|
| DOT | DOTCOM POSTAGE | Excluded from product ranking |
| POST | POSTAGE | Excluded from product ranking |
| M | Manual | Excluded from product ranking |
| m | Manual | Excluded from product ranking |
| AMAZONFEE | AMAZON FEE | Excluded from product ranking |
| B | Adjust bad debt | Excluded from product ranking |

Codes `DCGSSBOY` and `DCGSSGIRL` are kept because they map to real products (`BOYS PARTY BAG` and `GIRLS PARTY BAG`).

Service codes are only excluded from the product ranking; they are not removed from `cleaned_retail.csv` and remain in total Revenue.

Top 3 by revenue: 22423 (£174,157), 23843 (£168,470), 85123A (£104,463).

Top 3 by quantity: 23843, 23166, 22197.

Only 23843 appears in both top 3s. 22423 leads revenue but not quantity: high price, low volume. 23166 is #2 by quantity but only #6 by revenue: cheap, high volume. Conclusion: "best-selling" and "highest-revenue" are two different product sets.

### 3.5 Order value distribution
The boxplot shows a typical order is only a few hundred pounds; the upper (IQR) threshold is £1,006.11; the outlier tail stretches to £168K, which are wholesale orders, not data errors. This result feeds into the anomaly analysis.

## 4. Method
- Code: `src/eda.py`
- Charts: 5 files under `charts/`

## 5. Limitations
- Dataset covers 1 year, 1 UK store: do not generalize to the whole retail industry.
- December 2010 and December 2011 are partial months.
- Numeric product codes are not mapped to names/descriptions in this report.
- Descriptive analysis; no causal claims.

## 6. Charts
- `charts/revenue_monthly_line.png`
- `charts/revenue_country.png`
- `charts/top_products_quantity.png`
- `charts/top_products_revenue.png`
- `charts/order_value_boxplot.png`
