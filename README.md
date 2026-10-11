# PDS301m — E-commerce Analytics

Dự án phân tích dữ liệu thương mại điện tử cho môn PDS301m (team G3), sử dụng bộ dữ liệu UCI Online Retail.

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
├── data/                      # KHÔNG commit lên Git (xem docs/DATASET_STORAGE.md)
│   ├── raw/                   # đặt online_retail.xlsx tại đây
│   └── processed/             # cleaned_retail.csv, cancelled_retail.csv, ...
│
├── src/
│   ├── data_processor.py      # RetailDataProcessor: validation, cleaning,
│   │                          # cancelled-invoice separation, feature engineering
│   ├── anomaly_detector.py    # OrderAnomalyDetector: IQR Revenue/Quantity
│   │                          # anomaly, business impact, chart generation
│   ├── feature_engineering.py # RFM / customer feature engineering
│   ├── eda.py                 # Revenue & Product EDA (có main() chạy độc lập)
│   ├── reconcile.py           # KPI reconciliation (có main() chạy độc lập)
│   ├── business_rules.py      # business rules độc lập
│   └── scraper.py             # web scraping bổ sung (books.toscrape.com)
│
├── tests/
│   ├── test_data_processor.py
│   ├── test_anomaly_detector.py
│   ├── test_rfm.py
│   └── test_rfm_integration.py
│
├── notebooks/                 # exploration & deliverables; logic tái dùng
│   │                          # nằm ở src/, notebook chỉ import
│   ├── 04_customer_segmentation.ipynb   # RFM segmentation
│   ├── 05_python_oop_demo.ipynb        # Python/OOP demo
│   └── 06_final_integrated_analysis.ipynb  # final integration
│
├── charts/                    # PNG được track trong Git (xem quy ước đặt tên)
│
├── docs/
│   ├── DATASET_STORAGE.md     # dataset contract & reproducibility
│   ├── rfm_methodology.md     # phương pháp RFM
│   ├── rfm_followup_issue15.md
│   ├── issue22_handoff.md     # handoff notebook 06
│   └── iqr.svg
│
└── reports/
    ├── revenue_product_eda.md
    ├── kpi_reconciliation.md
    ├── final_analytics_report.md
    └── final_evidence_notes.md
```

## File nào được Git track, file nào phải tự chuẩn bị

| Nhóm | Git track | Lấy / tái tạo ở local |
|---|---|---|
| Source, tests, notebooks, charts, reports, docs | Có | |
| `data/raw/online_retail.xlsx` | Không | Tải từ UCI (link bên dưới), đặt đúng path |
| `data/processed/*.csv` | Không | Chạy pipeline / đặt file CSV của team vào đúng path |

`.gitignore` chỉ loại trừ `data/raw/*` và `data/processed/*` (ngoại trừ `.gitkeep`). Charts và reports **được track** để phục vụ review.

## Setup

Yêu cầu Python 3.9+.

```bash
python -m pip install -r requirements.txt
```

## Data Preparation

1. Tải UCI Online Retail dataset: https://archive.ics.uci.edu/dataset/352/online+retail
2. Đặt file tại `data/raw/online_retail.xlsx` (đúng tên file, chữ thường).
3. Chạy cleaning pipeline để tạo `data/processed/cleaned_retail.csv`,
   `data/processed/cancelled_retail.csv` (xem mục Run Pipeline).
4. File `data/processed/customer_segments.csv` được tạo bởi notebook 04.

Chi tiết data contract (schema, quy tắc Quantity/UnitPrice, chính sách duplicate,
công thức `Revenue = Quantity x UnitPrice`): `docs/DATASET_STORAGE.md`.

Lưu ý: dữ liệu `raw/` là bản gốc, không chỉnh sửa/ghi đè/xóa bản ghi bằng tay.
Dữ liệu `processed/` phải tái tạo được từ pipeline trong `src/` hoặc notebooks,
không sửa output bằng tay.

Quy ước dữ liệu của team: chỉ dùng UCI dataset cho phân tích doanh thu/khách hàng.

## Run

### Entry point chính

`notebooks/06_final_integrated_analysis.ipynb` là luồng phân tích tích hợp
end-to-end, import logic từ `src/` thay vì copy code.

```bash
jupyter notebook
```

Mở notebook 06 rồi **Restart Kernel → Run All**. Notebook tự tìm repo root
bằng pathlib, chạy được từ thư mục repo root hoặc `notebooks/`.
Input CSVs được đọc từ `data/processed/`; các assert trong notebook kiểm tra
KPI khớp với số liệu đã reconcile theo baseline.

### Run pipeline modules

Cleaning pipeline chạy qua class `RetailDataProcessor`:

```python
from pathlib import Path
from src.data_processor import RetailDataProcessor

p = RetailDataProcessor(Path("data/raw/online_retail.xlsx"))
df = p.load_and_explore()
p.clean_data(deduplicate=True, fill_guest=True)
p.engineer_features()
p.export_data(
    Path("data/processed/cleaned_retail.csv"),
    Path("data/processed/cancelled_retail.csv"),
)
```

Các module phân tích chạy độc lập từ repo root (cần `data/processed/*.csv` đã có):

```bash
python src/eda.py
python src/reconcile.py
```

`src/scraper.py` chạy scraping bổ sung (Books to Scrape: title/price/rating).

## Run Tests

Từ repository root:

```bash
python -m pytest -q
```

Tests hiện tại kiểm tra: data cleaning, duplicate handling, missing `InvoiceNo`,
invalid `InvoiceDate`, non-numeric `Quantity`/`UnitPrice`, cancelled invoices,
Revenue calculation, Revenue anomaly, Quantity anomaly, combined `IsAnomaly`,
empty DataFrame, zero-IQR edge case, anomaly CSV output, business impact
(Revenue/Quantity/Combined) và RFM logic.

`tests/test_rfm_integration.py` cần file `data/processed/cleaned_retail.csv`
ở local; test này tự skip khi file chưa có.

## Charts

Charts do notebook/source sinh ra, được track trong Git để review.

Quy ước đặt tên:

- `final_*.png`: chart do `notebooks/06_final_integrated_analysis.ipynb` (#22)
  sinh ra, dùng trong `reports/final_analytics_report.md` (#19).
- Các chart còn lại: output của từng phase phân tích (EDA #7, RFM #8,
  anomaly #6), được cite trong report tương ứng. Giữ lại làm evidence từng phase.

## Reports

- `reports/revenue_product_eda.md`: phân tích Revenue & Product (#7).
- `reports/kpi_reconciliation.md`: đối chiếu KPI giữa các pipeline (#18).
- `reports/final_analytics_report.md`: báo cáo phân tích cuối cùng (#19),
  kèm bảng traceability claim → evidence.
- `reports/final_evidence_notes.md`: ghi chú evidence bổ sung (#19).

Mỗi report nêu rõ câu hỏi nghiên cứu, nguồn và phạm vi dữ liệu, phương pháp,
kết quả, giới hạn và đường dẫn đến biểu đồ minh họa.

## Phương pháp

**RFM (Recency, Frequency, Monetary):** phân khúc khách hàng theo hành vi mua sắm.
Recency = ngày phân tích trừ ngày mua gần nhất; Frequency = số đơn hợp lệ trong kỳ;
Monetary = tổng giá trị mua trong kỳ.

**IQR (Interquartile Range):** phát hiện outlier. `IQR = Q3 - Q1`; outlier là giá trị
ngoài khoảng `[Q1 - 1.5*IQR, Q3 + 1.5*IQR]`. Order bị flag anomaly chỉ được đánh dấu
để review, không tự động xóa.

**ABC:** phân loại sản phẩm theo doanh thu. Tính tổng revenue từng sản phẩm, sắp xếp
giảm dần, tính tỷ lệ đóng góp và tỷ lệ tích lũy, rồi phân loại A/B/C theo ngưỡng.

## Branch Workflow

- `develop`: integration branch. Mọi thay đổi qua pull request trước khi merge.
- `main`: stable branch, hiện đang cũ (từ 24/09). Release `develop → main`
  chỉ thực hiện sau khi hoàn thành toàn bộ kiểm định P4 QA.
- Feature/fix branch tạo từ `develop`.

Không commit dataset lớn, file tạm, credential hoặc path máy cá nhân.

## Dataset

UCI Online Retail:

https://archive.ics.uci.edu/dataset/352/online+retail
