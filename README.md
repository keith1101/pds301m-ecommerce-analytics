# pds301m-ecommerce-analytics

Dự án phân tích dữ liệu thương mại điện tử sử dụng bộ dữ liệu **UCI Online Retail**.

## 1) Cấu trúc thư mục

```text
pds301m-ecommerce-analytics/
├── data/
│   ├── raw/
│   │   └── Online Retail.xlsx
│   └── processed/
├── notebooks/
├── src/
├── charts/
├── reports/
├── requirements.txt
├── .gitignore
└── data_specification.md
```

## 2) Thiết lập môi trường

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## 3) Dataset sử dụng

- Nguồn: UCI Machine Learning Repository - Online Retail
- File chuẩn lưu tại: `data/raw/Online Retail.xlsx`

Nếu cần tải lại dữ liệu:

```bash
curl -L "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx" -o "data/raw/Online Retail.xlsx"
```

## 4) Quy tắc xử lý dữ liệu thống nhất

Chi tiết đầy đủ nằm trong `data_specification.md`.

- Khảo sát cột/kiểu dữ liệu: InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country.
- Hóa đơn hủy: `InvoiceNo` bắt đầu bằng `C` -> loại khỏi phân tích doanh thu chuẩn.
- Giá trị không hợp lệ: loại các dòng có `Quantity <= 0` hoặc `UnitPrice <= 0`.
- Thiếu dữ liệu:
  - Bỏ dòng thiếu `CustomerID` cho phân tích khách hàng (RFM).
  - Bỏ dòng thiếu `Description` nếu phân tích theo sản phẩm.
- Định nghĩa doanh thu: **Revenue = Quantity × UnitPrice**.
- Output clean chuẩn: `data/processed/cleaned_retail.csv` gồm cột gốc + `Revenue`.

## 5) Analysis Specification (thống nhất phương pháp)

### 5.1 Phân tích doanh thu và sản phẩm
- Doanh thu theo tháng/quý.
- Top sản phẩm theo doanh thu và số lượng.
- Phân tích theo quốc gia.

### 5.2 Phân khúc khách hàng (RFM)
- **Recency**: số ngày từ lần mua gần nhất đến mốc tham chiếu.
- **Frequency**: số hóa đơn hợp lệ.
- **Monetary**: tổng Revenue.
- Chấm điểm RFM (ví dụ theo quantile) để nhóm khách hàng.

### 5.3 Phát hiện đơn hàng bất thường
- Cách 1: IQR trên `Revenue` theo đơn hàng.
- Cách 2: Z-score trên giá trị đơn hàng.
- Đối chiếu các đơn hàng ngoại lệ với Country/Customer để diễn giải.

### 5.4 Biểu đồ và file đầu ra
- Biểu đồ: doanh thu theo thời gian, top sản phẩm, phân bổ RFM, boxplot/point plot bất thường.
- Thư mục output:
  - `charts/`: ảnh biểu đồ
  - `reports/`: báo cáo tổng hợp (markdown/pdf)
  - `data/processed/cleaned_retail.csv`: dữ liệu đã làm sạch

Chi tiết phương pháp phân tích được chốt trong `analysis_specification.md`.

## 6) Trạng thái hoàn thành issue setup/spec

- [x] Repository có cấu trúc rõ ràng.
- [x] Thống nhất nguồn dữ liệu và quy tắc tính toán.
- [x] Xác định phương pháp phân tích để trả lời câu hỏi nghiên cứu chính.
