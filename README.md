# PDS301m — E-commerce Analytics

Dự án phân tích dữ liệu thương mại điện tử cho môn PDS301m sử dụng bộ dữ liệu UCI Online Retail.

Project hiện bao gồm data-cleaning pipeline, feature engineering, anomaly detection, RFM analysis, automated tests, notebooks và analysis artifacts.

## Mục tiêu

- Làm sạch và kiểm tra chất lượng dữ liệu giao dịch.
- Chuẩn hóa các trường dữ liệu quan trọng.
- Tạo Revenue và các đặc trưng phục vụ phân tích.
- Phân tích doanh thu và hành vi mua hàng.
- Phân khúc khách hàng bằng RFM.
- Phát hiện order anomaly theo Revenue và Quantity.
- Tạo output và biểu đồ có khả năng tái lập.

## Project Structure

```text
pds301m-ecommerce-analytics/
├── README.md
├── requirements.txt
├── pytest.ini
│
├── data/                  # file dữ liệu không commit lên git (xem docs/DATASET_STORAGE.md)
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── data_processor.py
│   ├── anomaly_detector.py
│   ├── feature_engineering.py
│   ├── eda.py
│   ├── business_rules.py
│   ├── reconcile.py
│   └── scraper.py
│
├── tests/
│   ├── test_data_processor.py
│   ├── test_anomaly_detector.py
│   ├── test_rfm.py
│   └── test_rfm_integration.py
│
├── notebooks/
│   ├── 04_customer_segmentation.ipynb
│   ├── 05_python_oop_demo.ipynb
│   └── 06_final_integrated_analysis.ipynb
│
├── charts/                # `final_*` = chart do notebook 06 sinh cho final report
│
├── docs/
│   ├── DATASET_STORAGE.md
│   ├── rfm_methodology.md
│   ├── rfm_followup_issue15.md
│   ├── issue22_handoff.md
│   └── iqr.svg
│
└── reports/
    ├── revenue_product_eda.md
    ├── kpi_reconciliation.md
    ├── final_analytics_report.md
    └── final_evidence_notes.md
```

## Entry points

- `notebooks/06_final_integrated_analysis.ipynb`: luồng phân tích tích hợp end-to-end (#22), import từ `src/`.
- Chạy độc lập từng module phân tích từ repo root: `python src/eda.py`, `python src/reconcile.py`.

## Data Pipeline

Pipeline chính:

```text
Raw Dataset
    ↓
Validation
    ↓
Duplicate Handling
    ↓
Cancelled Invoice Separation
    ↓
Invalid Quantity / UnitPrice Filtering
    ↓
Feature Engineering
    ↓
Order Aggregation
    ↓
Revenue + Quantity IQR Detection
    ↓
Business Impact
    ↓
CSV + Chart Outputs
```

## Anomaly Logic

Hai loại anomaly được phát hiện:

```text
IsRevenueAnomaly
IsQuantityAnomaly
```

Combined flag:

```text
IsAnomaly =
IsRevenueAnomaly OR IsQuantityAnomaly
```

Các order được gắn anomaly chỉ được đánh dấu để review, không tự động bị xóa.

## Setup

Cài dependencies:

```bash
python -m pip install -r requirements.txt
```

Dataset gốc cần được đặt tại:

```text
data/raw/online_retail.xlsx
```

## Run Pipeline

Từ repository root:

```bash
python src/main.py
```

Pipeline tạo:

```text
data/processed/cleaned_retail.csv
data/processed/cancelled_retail.csv
data/processed/anomaly_orders.csv
charts/revenue_boxplot.png
```

## Run Tests

```bash
python -m pytest -q
```

## Data Storage

Raw dataset và processed CSV không được commit vào Git.

Chi tiết reproducibility và dataset contract:

```text
docs/DATASET_STORAGE.md
```

Các chart phục vụ review/report được track trong Git.

## Branch Workflow

- `main`: stable branch.
- `develop`: integration branch.
- Feature/fix branch được tạo từ `develop`.
- Mọi thay đổi cần qua pull request trước khi merge vào `develop`.

## Dataset

UCI Online Retail:

https://archive.ics.uci.edu/dataset/352/online+retail