# Analysis Specification

## 1. Phân tích doanh thu và sản phẩm
- Revenue theo tháng/quý/năm.
- Top sản phẩm theo Revenue và Quantity.
- Cơ cấu doanh thu theo Country.

## 2. Phân khúc khách hàng theo RFM
- **Recency**: số ngày kể từ lần mua gần nhất.
- **Frequency**: số hóa đơn hợp lệ của khách hàng.
- **Monetary**: tổng Revenue của khách hàng.
- Chấm điểm theo quantile (1-4 hoặc 1-5), kết hợp thành nhóm khách hàng.

## 3. Phát hiện đơn hàng bất thường
- Tính tổng Revenue theo từng `InvoiceNo`.
- Phương pháp 1: IQR rule để phát hiện outlier.
- Phương pháp 2: Z-score để đánh dấu điểm bất thường.
- So sánh giao giữa 2 phương pháp để lấy danh sách bất thường đáng tin cậy.

## 4. Biểu đồ và đầu ra
- `charts/revenue_trend.png`
- `charts/top_products.png`
- `charts/rfm_segments.png`
- `charts/order_anomalies.png`
- `reports/final_report.md`
- `data/processed/cleaned_retail.csv`
