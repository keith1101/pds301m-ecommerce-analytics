# PDS301m — E-commerce Analytics

E-commerce data analytics pipeline and customer segmentation project for course PDS301m (Team G3), built upon the UCI Online Retail dataset.

The repository provides an end-to-end data processing pipeline, feature engineering, upper-tail IQR anomaly detection, tie-safe RFM customer segmentation, web scraping, automated test suites, analytical notebooks, and comprehensive technical reports.

## Objectives

- Clean, validate, and audit transactional data quality.
- Standardize core schema fields, data types, and missing value representations.
- Engineer line-item revenue and temporal features for analytics.
- Uncover multidimensional sales trends across time, geography, and product lines.
- Segment customer purchase behavior using the RFM model.
- Detect high-value wholesale order anomalies via upper-tail Interquartile Range (IQR).
- Ensure reproducible analytical artifacts, visualizations, and summary reports.

## Project Structure

```text
pds301m-ecommerce-analytics/
├── README.md
├── requirements.txt
├── pytest.ini
│
├── data/                      # Excluded from Git tracking (see docs/DATASET_STORAGE.md)
│   ├── raw/                   # Place online_retail.xlsx here
│   └── processed/             # cleaned_retail.csv, cancelled_retail.csv, etc.
│
├── src/
│   ├── data_processor.py      # RetailDataProcessor: validation, cleaning,
│   │                          # cancellation separation, feature engineering
│   ├── anomaly_detector.py    # OrderAnomalyDetector: IQR Revenue/Quantity
│   │                          # anomaly detection, business impact, plotting
│   ├── feature_engineering.py # RFM segmentation & customer feature engineering
│   ├── eda.py                 # Revenue & Product EDA (standalone CLI main)
│   ├── reconcile.py           # KPI reconciliation & validation (standalone CLI main)
│   ├── business_rules.py      # Standalone business rule functions
│   └── scraper.py             # Books to Scrape web scraper (title/price/rating)
│
├── tests/
│   ├── test_data_processor.py
│   ├── test_anomaly_detector.py
│   ├── test_business_rules.py
│   ├── test_rfm.py
│   └── test_rfm_integration.py
│
├── notebooks/                 # Exploratory analyses & final deliverables
│   ├── 04_customer_segmentation.ipynb   # RFM segmentation workflow
│   ├── 05_python_oop_demo.ipynb        # Python OOP & core data structure demo
│   └── 06_final_integrated_analysis.ipynb  # End-to-end integrated analysis
│
├── charts/                    # High-resolution PNG figures tracked in Git
│
├── docs/
│   ├── DATASET_STORAGE.md     # Data contract & reproducibility specifications
│   ├── p4_traceability.md     # 16-requirement traceability audit matrix
│   ├── rfm_methodology.md     # RFM mathematical methodology & scoring
│   ├── rfm_followup_issue15.md
│   ├── issue22_handoff.md     # Notebook 06 integration handoff notes
│   └── iqr.svg
│
└── reports/
    ├── PDS301m_G3_BaoCaoTongKet.docx  # Final academic project report (DOCX)
    ├── revenue_product_eda.md         # Revenue & Product EDA report
    ├── kpi_reconciliation.md          # Multi-pipeline KPI reconciliation report
    ├── final_analytics_report.md      # Final integrated analytics report
    └── final_evidence_notes.md        # Traceability & evidence notes
```

## Tracked Files vs. Local Datasets

| Category | Tracked in Git | Local Acquisition / Reproduction |
|---|---|---|
| Source code, tests, notebooks, charts, reports, docs | Yes | Included in repository clone |
| `data/raw/online_retail.xlsx` | No | Download from UCI Machine Learning Repository (link below) |
| `data/processed/*.csv` | No | Generated via pipeline or reproduced using notebooks |

`.gitignore` excludes `data/raw/*` and `data/processed/*` (preserving `.gitkeep`). Charts and report artifacts are **tracked in Git** for academic grading and peer verification.

## Setup

Requires Python 3.9+.

```bash
python -m pip install -r requirements.txt
```

## Data Preparation

1. Download the UCI Online Retail dataset: https://archive.ics.uci.edu/dataset/352/online+retail
2. Place the file at `data/raw/online_retail.xlsx` (lowercase filename).
3. Execute the data cleaning pipeline to generate `data/processed/cleaned_retail.csv` and `data/processed/cancelled_retail.csv` (see [Run Pipeline Modules](#run-pipeline-modules)).
4. Customer segments (`data/processed/customer_segments.csv`) are produced by notebook `04_customer_segmentation.ipynb` or via `src/feature_engineering.py`.

For comprehensive data contract specifications (schema types, Quantity/UnitPrice filtering rules, deduplication policies, and the `Revenue = Quantity * UnitPrice` convention), refer to `docs/DATASET_STORAGE.md`.

*Note:* Raw data in `data/raw/` is treated as immutable ground truth. All processed data in `data/processed/` must be deterministically reproducible from code without manual edits.

## Execution

### Primary Entry Point

`notebooks/06_final_integrated_analysis.ipynb` serves as the end-to-end integration workflow, consuming modular components from `src/`:

```bash
jupyter notebook
```

Open notebook 06 and run **Restart Kernel → Run All**. The notebook resolves repository root paths dynamically via `pathlib`, executing seamlessly from either the project root or the `notebooks/` subfolder. Built-in assertions verify that all intermediate KPIs reconcile exactly with established baselines.

### Run Pipeline Modules

Execute data cleaning via the `RetailDataProcessor` class:

```python
from pathlib import Path
from src.data_processor import RetailDataProcessor

processor = RetailDataProcessor(Path("data/raw/online_retail.xlsx"))
df = processor.load_and_explore()
processor.clean_data(deduplicate=True, fill_guest=True)
processor.engineer_features()
processor.export_data(
    Path("data/processed/cleaned_retail.csv"),
    Path("data/processed/cancelled_retail.csv"),
)
```

Run standalone analysis modules from the repository root (requires generated `data/processed/*.csv` files):

```bash
python src/eda.py
python src/reconcile.py
```

Run the supplementary web scraper (`books.toscrape.com`):

```bash
python src/scraper.py
```

## Running Automated Tests

Run the test suite from the repository root:

```bash
python -m pytest -q
```

The test suite covers:
- Core data validation, deduplication audits, and missing identifier handling.
- Timestamp parsing and non-positive `Quantity`/`UnitPrice` filtering.
- Cancellation prefix separation (`C`-prefixed invoices).
- Line-item `Revenue` calculation and aggregation.
- Upper-tail IQR anomaly detection (Revenue, Quantity, and combined flags).
- Empty dataset and zero-IQR boundary conditions.
- Business impact quantification across normal vs. anomaly orders.
- Tie-safe percentile RFM scoring and 6-segment precedence hierarchies.
- Production dataset KPI reconciliation.

## Visualizations

All figures generated by pipelines and notebooks are stored in `charts/` and tracked in version control:

- `final_*.png`: Production visualizations generated by `notebooks/06_final_integrated_analysis.ipynb` and referenced in final reports.
- Exploratory charts: Phase-specific outputs (EDA, RFM distribution, order anomaly boxplots) retained as auditable artifacts.

## Reports & Documentation

- `reports/PDS301m_G3_BaoCaoTongKet.docx`: Academic project summary report with formal formatting, embedded charts, and comprehensive KPI reconciliations.
- `reports/revenue_product_eda.md`: In-depth analysis of temporal patterns, top products, and geographical distribution.
- `reports/kpi_reconciliation.md`: Multi-pipeline KPI reconciliation and cross-module consistency validation.
- `reports/final_analytics_report.md`: Technical analytics report with claim-to-evidence traceability.
- `docs/p4_traceability.md`: Complete audit matrix mapping all 16 project requirements to verified code locations.

## Methodology

### RFM (Recency, Frequency, Monetary)
Customer behavioral segmentation based on three pillars:
- **Recency ($R$):** Days elapsed from customer's latest purchase to reference baseline date (2011-12-10).
- **Frequency ($F$):** Number of distinct valid sales transactions.
- **Monetary ($M$):** Cumulative spending across valid sales transactions.
Scores are assigned from 1 to 5 using tie-safe percentile rank binning and mapped to 6 business segments (*Champions*, *Loyal Customers*, *At Risk*, *Potential Loyalists*, *Hibernating*, *Others*).

### IQR Anomaly Detection
Outlier identification across aggregated invoices using the upper-tail Interquartile Range:
$$\text{Upper Bound} = Q_3 + 1.5 \times \text{IQR}$$
Orders exceeding threshold limits in Revenue (£1,006.11) or Quantity (636.5 units) are flagged for business review as legitimate B2B wholesale orders rather than discarded.

### ABC & Product Concentration
Classification of catalog items by revenue contribution. Products are sorted descending by cumulative revenue share to distinguish high-impact SKUs from volume-driven items (after filtering out freight and service charges such as `DOT`, `POST`, `AMAZONFEE`).

## Branch Workflow

- `develop`: Integration branch. All features and bugfixes are integrated and verified here.
- `main`: Production release branch. Releases from `develop → main` are merged following full QA audit and test verification.
- Feature branches follow standard Git naming conventions (`feature/<name>-<topic>`).

## Dataset Reference

UCI Machine Learning Repository — Online Retail Dataset:
https://archive.ics.uci.edu/dataset/352/online+retail
